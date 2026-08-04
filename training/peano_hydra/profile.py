"""Frozen semantic identity for the first Peano Hydra campaign profile.

The profile is data, not proof authority.  It records the exact object
language and claim boundary used by Hydra while the independent Peano kernel
remains the sole authority for a positive theorem.  This module deliberately
uses strict, canonical JSON so a profile mutation cannot hide behind key
order, whitespace, duplicate keys, or a non-finite JSON extension.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Literal

from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
)
from peano_lab.kernel import formulas as kernel_formulas
from peano_lab.kernel import proofs as kernel_proofs
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from training.peano_hydra.profile_theorem_v1 import (
    FrozenProfileTheoremError,
    MAX_DECIMAL_NUMERAL as PROFILE_V1_V2_MAX_NUMERAL,
    MAX_SOURCE_CHARACTERS as PROFILE_V1_V2_MAX_INPUT,
    canonicalize_profile_formula as _canonicalize_profile_formula_v1_v2,
    canonicalize_profile_theorem as _canonicalize_profile_theorem_v1_v2,
)


SEMANTIC_PROFILE_FORMAT = "peano-hydra-semantic-profile"
SEMANTIC_PROFILE_VERSION = 2
SEMANTIC_PROFILE_ID = "peano-lab-ha-intuitionistic-v2"
SEMANTIC_PROFILE_PATH = Path(__file__).with_name("semantic-profile-v2.json")
SEMANTIC_PROFILE_V1_VERSION = 1
SEMANTIC_PROFILE_V1_ID = "peano-lab-ha-intuitionistic-v1"
SEMANTIC_PROFILE_V1_PATH = Path(__file__).with_name("semantic-profile-v1.json")
SEMANTIC_PROFILE_V1_DOCUMENT_SHA256 = (
    "7defa4113b3d64909f48ce7717f06c163014c5ae910c8643797ab308798ea5ac"
)
SEMANTIC_PROFILE_V1_SHA256 = (
    "058b1644b066967919dae092e5e562b8845e4dd8415fff31d7cd209d51bc9e43"
)
# Pinned below once ``semantic-profile-v2.json`` is assembled from the frozen
# v1 fragment plus the exact H0.1b evidence contract.  Unlike
# ``semantic_profile_sha256()``, registry dispatch uses this immutable value
# and therefore does not accidentally reinterpret historical records through
# a later active profile.
SEMANTIC_PROFILE_V2_DOCUMENT_SHA256 = (
    "e19162d0e78779d34e5e02166eeb109c5a75091b4692fe37577a7fa47ff29287"
)
SEMANTIC_PROFILE_V2_SHA256 = (
    "4f2713e6a21e6261bbefe5991ef545e6356807e7042c6b2c7c07183e142c3b4b"
)
# Immutable H0.1b values embedded by semantic profile v2.  They are not
# aliases of whichever result schema a future active profile imports.
_PROFILE_V2_RESULT_FORMAT = "peano-hydra-result"
_PROFILE_V2_RESULT_VERSION = 1
_PROFILE_V2_HASH_PREIMAGE_FORMAT = "peano-hydra-result-hash-preimage"
_PROFILE_V2_HASH_PREIMAGE_VERSION = 1
_PROFILE_V2_RESULT_SCHEMA_FORMAT = "peano-hydra-result-schema"
_PROFILE_V2_RESULT_SCHEMA_ID = "peano-hydra-result-v1"
_PROFILE_V2_RESULT_SCHEMA_SHA256 = (
    "cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26"
)
_PROFILE_V2_RESULT_SCHEMA_VERSION = 1
MAX_SEMANTIC_PROFILE_BYTES = 1_000_000
# Backward-compatible names for the v1/v2 theorem transport limits.  Active
# live-alignment diagnostics deliberately read the browser module lazily.
MAX_INPUT = PROFILE_V1_V2_MAX_INPUT
MAX_NUMERAL = PROFILE_V1_V2_MAX_NUMERAL

EvidenceKind = Literal["proved", "unknown"]


class SemanticProfileError(ValueError):
    """The profile or an attempted in-profile theorem is malformed."""


def _live_input_admission() -> dict[str, object]:
    """Describe the current browser pre-parser target-admission rules."""

    from peano_lab.ui import prove as live_prove

    return {
        "character_measure": "unicode-code-points",
        "decision_claim": False,
        "decimal_numeral_comparison": "normalized-base10-value",
        "forbidden_unicode_categories": ["Cc", "Cf", "Cs", "Zl", "Zp"],
        "hash_character": "forbidden",
        "kind": "source-preflight-v1",
        "line_policy": "one-line-no-outer-whitespace",
        "max_decimal_numeral": live_prove.MAX_NUMERAL,
        "max_source_characters": live_prove.MAX_INPUT,
        "nonempty": True,
        "numeral_literal_boundary": (
            "not-preceded-by-word-character-apostrophe-or-hash"
        ),
    }


def _profile_v1_v2_input_admission() -> dict[str, object]:
    """Return the immutable admission data recorded by profiles v1/v2."""

    return {
        "character_measure": "unicode-code-points",
        "decision_claim": False,
        "decimal_numeral_comparison": "normalized-base10-value",
        "forbidden_unicode_categories": ["Cc", "Cf", "Cs", "Zl", "Zp"],
        "hash_character": "forbidden",
        "kind": "source-preflight-v1",
        "line_policy": "one-line-no-outer-whitespace",
        "max_decimal_numeral": PROFILE_V1_V2_MAX_NUMERAL,
        "max_source_characters": PROFILE_V1_V2_MAX_INPUT,
        "nonempty": True,
        "numeral_literal_boundary": (
            "not-preceded-by-word-character-apostrophe-or-hash"
        ),
    }


_REGISTERED_PROFILE_V1: dict[str, object] = {
    "arithmetic": {
        "axioms": [
            {"formula": "∀ x. ¬S x = 0", "name": "PA1"},
            {"formula": "∀ x. ∀ y. S x = S y → x = y", "name": "PA2"},
            {"formula": "∀ x. x + 0 = x", "name": "PA3"},
            {"formula": "∀ x. ∀ y. x + S y = S (x + y)", "name": "PA4"},
            {"formula": "∀ x. x · 0 = 0", "name": "PA5"},
            {"formula": "∀ x. ∀ y. x · S y = x · y + x", "name": "PA6"},
        ],
        "induction": {
            "base": "open(motive,0,Zero)",
            "conclusion": "Forall(motive)",
            "kind": "unrestricted-formula-schema",
            "motive_placeholder": "Var(0)",
            "step": (
                "Forall(Imp(motive,open(shift(motive,1,cutoff=1),"
                "0,Succ(Var(0)))))"
            ),
        },
    },
    "authority": {
        "certificate_representation": "python-dataclass-repr-with-cut-v2",
        "classical_checker": "forbidden",
        "context": "empty",
        "goal": "original",
        "positive": "peano_lab.kernel.checker.check",
    },
    "binding": {
        "alpha_equivalence": "structural-equality-after-de-bruijn-conversion",
        "free_surface_name_order": "first-occurrence",
        "index_type": "nonnegative-integer",
        "index_zero": "innermost-term-binder",
        "representation": "de-bruijn",
        "top_level_scope_depth": 0,
        "top_level_well_scoped": True,
    },
    "calculus": {
        "classical": False,
        "context_order": "newest-hypothesis-first",
        "cut": "self-contained-implication-cut",
        "dne": False,
        "equality_substitution": (
            "Gamma|-e:s=t;Gamma|-body:open(P,0,s)=>"
            "Gamma|-EqSubst(P,e,body):open(P,0,t)"
        ),
        "logic": "intuitionistic-natural-deduction",
        "proof_constructors": [
            "Hyp",
            "ImpIntro",
            "ImpElim",
            "Cut",
            "AndIntro",
            "AndElimL",
            "AndElimR",
            "OrIntroL",
            "OrIntroR",
            "OrElim",
            "BotElim",
            "ForallIntro",
            "ForallElim",
            "ExistsIntro",
            "ExistsElim",
            "EqRefl",
            "EqSym",
            "EqTrans",
            "CongS",
            "CongAdd",
            "CongMul",
            "EqSubst",
            "Axiom",
            "Ind",
        ],
        "rules": {
            "AndElimL": "Gamma|-p:And(A,B)=>Gamma|-AndElimL(p):A",
            "AndElimR": "Gamma|-p:And(A,B)=>Gamma|-AndElimR(p):B",
            "AndIntro": "Gamma|-p:A;Gamma|-q:B=>Gamma|-AndIntro(p,q):And(A,B)",
            "Axiom": "name-in-PA1-through-PA6=>Gamma|-Axiom(name):axiom(name)",
            "BotElim": "Gamma|-p:Bot=>Gamma|-BotElim(p):A",
            "CongAdd": "Gamma|-p:a=b;Gamma|-q:c=d=>Gamma|-CongAdd(p,q):Add(a,c)=Add(b,d)",
            "CongMul": "Gamma|-p:a=b;Gamma|-q:c=d=>Gamma|-CongMul(p,q):Mul(a,c)=Mul(b,d)",
            "CongS": "Gamma|-p:a=b=>Gamma|-CongS(p):Succ(a)=Succ(b)",
            "Cut": "Gamma|-lemma:P;P,Gamma|-body:C=>Gamma|-Cut(P,C,lemma,body):C",
            "EqRefl": "Gamma|-EqRefl(t):t=t",
            "EqSubst": "Gamma|-e:s=t;Gamma|-p:open(P,0,s)=>Gamma|-EqSubst(P,e,p):open(P,0,t)",
            "EqSym": "Gamma|-p:a=b=>Gamma|-EqSym(p):b=a",
            "EqTrans": "Gamma|-p:a=b;Gamma|-q:b=c=>Gamma|-EqTrans(p,q):a=c",
            "ExistsElim": (
                "Gamma|-p:Exists(A);A,shift(Gamma,1)|-body:shift(C,1)=>"
                "Gamma|-ExistsElim(p,body):C"
            ),
            "ExistsIntro": "Gamma|-p:open(A,0,t)=>Gamma|-ExistsIntro(t,p):Exists(A)",
            "ForallElim": "Gamma|-p:Forall(A)=>Gamma|-ForallElim(p,t):open(A,0,t)",
            "ForallIntro": "shift(Gamma,1)|-body:A=>Gamma|-ForallIntro(body):Forall(A)",
            "Hyp": "Gamma[i]=A=>Gamma|-Hyp(i):A",
            "ImpElim": "Gamma|-f:Imp(A,B);Gamma|-a:A=>Gamma|-ImpElim(f,a):B",
            "ImpIntro": "A,Gamma|-body:B=>Gamma|-ImpIntro(body):Imp(A,B)",
            "Ind": (
                "Gamma|-base:open(P,0,Zero);Gamma|-step:Forall(Imp(P,"
                "open(shift(P,1,cutoff=1),0,Succ(Var(0)))))=>"
                "Gamma|-Ind(P,base,step):Forall(P)"
            ),
            "OrElim": "Gamma|-p:Or(A,B);A,Gamma|-l:C;B,Gamma|-r:C=>Gamma|-OrElim(p,l,r):C",
            "OrIntroL": "Gamma|-p:A=>Gamma|-OrIntroL(p):Or(A,B)",
            "OrIntroR": "Gamma|-p:B=>Gamma|-OrIntroR(p):Or(A,B)",
        },
    },
    "claim": {
        "decision_fragment": None,
        "decision_procedure": False,
        "decision_resource_bounds": None,
        "judgement": "empty-context-derivability",
        "kind": "sound-theorem-prover",
        "not_theorem_supported": False,
    },
    "evidence": {
        "additional_fields_policy": "not-yet-frozen",
        "common_required": [
            "format",
            "v",
            "kind",
            "semantic_profile_sha256",
            "original_theorem",
            "original_theorem_sha256",
            "run_evidence_sha256",
        ],
        "format": "peano-hydra-result",
        "hash_preimages": "not-yet-frozen",
        "kinds": ["proved", "unknown"],
        "not_theorem": {
            "publication": "forbidden",
            "supported": False,
        },
        "proved": {
            "authority": "empty-context-intuitionistic-kernel-original-goal",
            "required": [
                "certificate_representation",
                "certificate_sha256",
                "certificate_nodes",
                "certificate_depth",
                "kernel_identity_sha256",
                "replay_evidence_sha256",
                "kernel_accepted",
            ],
            "required_constants": {"kernel_accepted": True},
        },
        "schema_status": "required-field-draft",
        "unknown": {
            "forbidden": [
                "certificate_representation",
                "certificate_sha256",
                "certificate_nodes",
                "certificate_depth",
                "kernel_accepted",
                "negative_evidence_sha256",
            ],
            "meaning": "no-accepted-certificate-and-no-negative-theoremhood-claim",
            "required": ["reason"],
        },
        "v": 1,
    },
    "format": SEMANTIC_PROFILE_FORMAT,
    "id": SEMANTIC_PROFILE_V1_ID,
    "input": {
        "canonical_binder_candidates": [
            "x",
            "y",
            "z",
            "n",
            "m",
            "k",
            "i",
            "j",
            "u",
            "v",
            "w",
        ],
        "canonical_binder_fallback": (
            "x{least-nonnegative-integer-not-already-used}"
        ),
        "canonical_form": "canonical-unicode-surface-v1",
        "canonical_tokens": {
            "addition": "+",
            "bottom": "⊥",
            "conjunction": "∧",
            "equality": "=",
            "exists": "∃",
            "forall": "∀",
            "implication": "→",
            "multiplication": "·",
            "negation": "¬",
            "order": "≤",
            "successor": "S",
            "zero": "0",
        },
        "canonicalization": (
            "source-preflight;parse;reject-free-names;"
            "require-well-scoped-at-depth-0;pretty;"
            "reparse-and-require-structural-equality"
        ),
        "explicit_de_bruijn_target_syntax": False,
        "normal_form_required_in_artifacts": True,
        "operational_admission": _profile_v1_v2_input_admission(),
        "precedence_associativity": [
            "quantifiers-widest-scope",
            "implication-right-associative",
            "disjunction-left-associative",
            "conjunction-left-associative",
            "negation-prefix",
            "equality-nonassociative",
            "addition-left-associative",
            "multiplication-left-associative",
            "successor-prefix",
        ],
        "target": "closed-core-formula",
    },
    "substitution": {
        "equal_case": "Var(index+depth)->shift(replacement,depth)",
        "formula_structural_recursion": (
            "Eq:recurse-terms;Bot:unchanged;Imp/And/Or:recurse-both;"
            "Forall/Exists:recurse-body-with-depth+1"
        ),
        "greater_case": "Var(k),k>index+depth->Var(k-1)",
        "id": "capture-avoiding-open-one-slot-v1",
        "less_case": "unchanged",
        "shift_formula_structural_recursion": (
            "Eq:shift-terms;Bot:unchanged;Imp/And/Or:recurse-both;"
            "Forall/Exists:recurse-body-with-cutoff+1"
        ),
        "shift_term_structural_recursion": (
            "Zero:unchanged;Succ:recurse;Add/Mul:recurse-both"
        ),
        "shift_variable_case": "Var(k),k>=cutoff->Var(k+by);otherwise-unchanged",
        "term_structural_recursion": (
            "Zero:unchanged;Succ:recurse;Add/Mul:recurse-both"
        ),
    },
    "syntax": {
        "formulas": [
            "Eq(left,right)",
            "Bot",
            "Imp(antecedent,consequent)",
            "And(left,right)",
            "Or(left,right)",
            "Forall(body)",
            "Exists(body)",
        ],
        "terms": [
            "Var(index)",
            "Zero",
            "Succ(term)",
            "Add(left,right)",
            "Mul(left,right)",
        ],
    },
    "translations": {
        "external": [],
        "surface": [
            {
                "domain": f"0<=n<={PROFILE_V1_V2_MAX_NUMERAL}",
                "from": "decimal n",
                "name": "numeral",
                "to": "Succ^n(Zero)",
            },
            {
                "from": "~A or ¬A",
                "name": "negation",
                "to": "Imp(A,Bot)",
            },
            {
                "from": "a<=b or a≤b",
                "name": "order",
                "to": "Exists(Eq(Add(Var(0),lift(a,1)),lift(b,1)))",
            },
            {
                "from": "*,->,/\\,\\/,forall,exists,bot,false",
                "name": "ascii-aliases",
                "to": "Mul,Imp,And,Or,Forall,Exists,Bot,Bot",
            },
        ],
    },
    "v": SEMANTIC_PROFILE_V1_VERSION,
}


_REGISTERED_PROFILE: dict[str, object] = deepcopy(_REGISTERED_PROFILE_V1)
_REGISTERED_PROFILE["id"] = SEMANTIC_PROFILE_ID
_REGISTERED_PROFILE["v"] = SEMANTIC_PROFILE_VERSION
assert type(_REGISTERED_PROFILE["authority"]) is dict
_REGISTERED_PROFILE["authority"]["certificate_representation"] = "peano-lab-v2"
_REGISTERED_PROFILE["evidence"] = {
    "additional_fields_policy": "forbidden",
    "canonical_json": "peano-hydra-canonical-json-v1",
    "format": _PROFILE_V2_RESULT_FORMAT,
    "hash_algorithm": "sha256",
    "hash_preimage": {
        "format": _PROFILE_V2_HASH_PREIMAGE_FORMAT,
        "v": _PROFILE_V2_HASH_PREIMAGE_VERSION,
    },
    "kinds": ["proved", "unknown"],
    "not_theorem": {
        "publication": "forbidden",
        "supported": False,
    },
    "schema": {
        "format": _PROFILE_V2_RESULT_SCHEMA_FORMAT,
        "id": _PROFILE_V2_RESULT_SCHEMA_ID,
        "sha256": _PROFILE_V2_RESULT_SCHEMA_SHA256,
        "v": _PROFILE_V2_RESULT_SCHEMA_VERSION,
    },
    "schema_status": "exact-content-addressed",
    "unknown_meaning": (
        "no-accepted-certificate-and-no-negative-theoremhood-claim"
    ),
    "v": _PROFILE_V2_RESULT_VERSION,
}


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise SemanticProfileError(f"profile is not strict JSON: {exc}") from None


def _canonical_document_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise SemanticProfileError(f"profile is not strict JSON: {exc}") from None


_REGISTERED_CANONICAL_BYTES = _canonical_json_bytes(_REGISTERED_PROFILE)
_REGISTERED_DOCUMENT_BYTES = _canonical_document_bytes(_REGISTERED_PROFILE)
_REGISTERED_V1_CANONICAL_BYTES = _canonical_json_bytes(_REGISTERED_PROFILE_V1)
_REGISTERED_V1_DOCUMENT_BYTES = _canonical_document_bytes(_REGISTERED_PROFILE_V1)


def validate_semantic_profile(value: object) -> dict[str, object]:
    """Return a detached active v2 profile or reject every deviation."""

    if type(value) is not dict:
        raise SemanticProfileError("semantic profile must be one exact JSON object")
    if _canonical_json_bytes(value) != _REGISTERED_CANONICAL_BYTES:
        raise SemanticProfileError("semantic profile does not match registered v2")
    detached = json.loads(_REGISTERED_CANONICAL_BYTES.decode("utf-8"))
    if type(detached) is not dict:  # pragma: no cover - construction invariant
        raise RuntimeError("registered semantic profile is not an object")
    return detached


def validate_semantic_profile_v1(value: object) -> dict[str, object]:
    """Validate the byte-preserved historical H0.1a profile v1 value."""

    if type(value) is not dict:
        raise SemanticProfileError("semantic profile v1 must be one exact JSON object")
    if _canonical_json_bytes(value) != _REGISTERED_V1_CANONICAL_BYTES:
        raise SemanticProfileError("semantic profile does not match historical v1")
    detached = json.loads(_REGISTERED_V1_CANONICAL_BYTES.decode("utf-8"))
    if type(detached) is not dict:  # pragma: no cover - construction invariant
        raise RuntimeError("historical semantic profile is not an object")
    return detached


def _validate_kernel_alignment(profile: dict[str, object]) -> None:
    """Fail closed if the registered claims drift from the live kernel."""

    from peano_lab.kernel.checker import axiom_formula
    from peano_lab.kernel.formulas import pretty_formula

    arithmetic = profile.get("arithmetic")
    calculus = profile.get("calculus")
    if type(arithmetic) is not dict or type(calculus) is not dict:
        raise SemanticProfileError("registered profile lost its kernel schema")
    recorded_axioms = arithmetic.get("axioms")
    if type(recorded_axioms) is not list:
        raise SemanticProfileError("registered profile has malformed axioms")
    actual_axioms: list[dict[str, str]] = []
    for name in ("PA1", "PA2", "PA3", "PA4", "PA5", "PA6"):
        formula = axiom_formula(name)
        if formula is None or not well_scoped_formula(formula):
            raise SemanticProfileError(f"kernel axiom {name} is absent or open")
        actual_axioms.append({"formula": pretty_formula(formula, []), "name": name})
    if recorded_axioms != actual_axioms:
        raise SemanticProfileError("registered PA axioms disagree with the kernel")

    recorded_constructors = calculus.get("proof_constructors")
    actual_constructors = [
        name for name in kernel_proofs.__all__ if name not in {"Proof", "DNE"}
    ]
    if recorded_constructors != actual_constructors:
        raise SemanticProfileError(
            "registered intuitionistic proof constructors disagree with the kernel"
        )
    rules = calculus.get("rules")
    if type(rules) is not dict or set(rules) != set(actual_constructors):
        raise SemanticProfileError(
            "registered proof rules do not cover every intuitionistic constructor"
        )
    if calculus.get("classical") is not False or calculus.get("dne") is not False:
        raise SemanticProfileError("registered profile must remain intuitionistic")
    input_profile = profile.get("input")
    if type(input_profile) is not dict or tuple(
        input_profile.get("canonical_binder_candidates", ())
    ) != tuple(kernel_formulas._BINDER_NAMES):
        raise SemanticProfileError(
            "registered canonical binder policy disagrees with the kernel printer"
        )
    if input_profile.get("operational_admission") != _live_input_admission():
        raise SemanticProfileError(
            "registered target admission disagrees with the live transport guards"
        )
    claim = profile.get("claim")
    if (
        type(claim) is not dict
        or claim.get("decision_resource_bounds") is not None
        or _live_input_admission()["decision_claim"] is not False
    ):
        raise SemanticProfileError(
            "operational target admission must not become a decision claim"
        )
    if profile.get("v") == SEMANTIC_PROFILE_VERSION:
        from training.peano_hydra.result_schema import result_schema_identity

        evidence = profile.get("evidence")
        expected_schema = {
            "format": _PROFILE_V2_RESULT_SCHEMA_FORMAT,
            "id": _PROFILE_V2_RESULT_SCHEMA_ID,
            "sha256": _PROFILE_V2_RESULT_SCHEMA_SHA256,
            "v": _PROFILE_V2_RESULT_SCHEMA_VERSION,
        }
        if (
            type(evidence) is not dict
            or evidence.get("schema_status") != "exact-content-addressed"
            or evidence.get("additional_fields_policy") != "forbidden"
            or evidence.get("schema") != expected_schema
            or evidence.get("kinds") != ["proved", "unknown"]
            or evidence.get("not_theorem")
            != {"publication": "forbidden", "supported": False}
        ):
            raise SemanticProfileError(
                "registered profile lost its exact result-schema binding"
            )
        if result_schema_identity() != expected_schema:
            raise SemanticProfileError(
                "registered result-schema artifact disagrees with profile v2"
            )


def semantic_profile_v2() -> dict[str, object]:
    """Load frozen v2 bytes without consulting the current live kernel."""

    try:
        raw = SEMANTIC_PROFILE_PATH.read_bytes()
    except OSError as exc:
        raise SemanticProfileError("cannot read registered semantic profile") from exc
    if len(raw) > MAX_SEMANTIC_PROFILE_BYTES:
        raise SemanticProfileError("registered semantic profile exceeds its size limit")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise SemanticProfileError(f"registered semantic profile is invalid: {exc}") from None
    profile = validate_semantic_profile(value)
    if raw != _REGISTERED_DOCUMENT_BYTES:
        raise SemanticProfileError("registered semantic profile is not canonical JSON")
    if hashlib.sha256(raw).hexdigest() != SEMANTIC_PROFILE_V2_DOCUMENT_SHA256:
        raise SemanticProfileError("semantic profile v2 bytes drifted")
    digest = hashlib.sha256(_canonical_json_bytes(profile)).hexdigest()
    if digest != SEMANTIC_PROFILE_V2_SHA256:
        raise SemanticProfileError("semantic profile v2 digest drifted")
    return profile


def semantic_profile() -> dict[str, object]:
    """Load the active v2 artifact and diagnose alignment with the live kernel."""

    profile = semantic_profile_v2()
    _validate_kernel_alignment(profile)
    return profile


def semantic_profile_v1() -> dict[str, object]:
    """Load the canonical historical v1 artifact without promoting its draft."""

    try:
        raw = SEMANTIC_PROFILE_V1_PATH.read_bytes()
    except OSError as exc:
        raise SemanticProfileError("cannot read historical semantic profile v1") from exc
    if len(raw) > MAX_SEMANTIC_PROFILE_BYTES:
        raise SemanticProfileError("historical semantic profile exceeds its size limit")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise SemanticProfileError(
            f"historical semantic profile is invalid: {exc}"
        ) from None
    profile = validate_semantic_profile_v1(value)
    if raw != _REGISTERED_V1_DOCUMENT_BYTES:
        raise SemanticProfileError(
            "historical semantic profile v1 is not canonical JSON"
        )
    if hashlib.sha256(raw).hexdigest() != SEMANTIC_PROFILE_V1_DOCUMENT_SHA256:
        raise SemanticProfileError("historical semantic profile v1 bytes drifted")
    return profile


def semantic_profile_sha256() -> str:
    """Hash the canonical JSON value, excluding display whitespace/newline."""

    profile = semantic_profile()
    digest = hashlib.sha256(_canonical_json_bytes(profile)).hexdigest()
    if digest != SEMANTIC_PROFILE_V2_SHA256:
        raise SemanticProfileError("active semantic profile v2 digest drifted")
    return digest


def semantic_profile_v2_sha256() -> str:
    """Return v2's semantic digest without a live-kernel alignment check."""

    profile = semantic_profile_v2()
    digest = hashlib.sha256(_canonical_json_bytes(profile)).hexdigest()
    if digest != SEMANTIC_PROFILE_V2_SHA256:
        raise SemanticProfileError("semantic profile v2 digest drifted")
    return digest


def semantic_profile_v1_sha256() -> str:
    """Return and verify the historical v1 semantic digest."""

    profile = semantic_profile_v1()
    digest = hashlib.sha256(_canonical_json_bytes(profile)).hexdigest()
    if digest != SEMANTIC_PROFILE_V1_SHA256:
        raise SemanticProfileError("historical semantic profile v1 digest drifted")
    return digest


def semantic_profile_identity() -> dict[str, object]:
    """Return the complete small identity bound into downstream artifacts."""

    return {
        "format": SEMANTIC_PROFILE_FORMAT,
        "v": SEMANTIC_PROFILE_VERSION,
        "id": SEMANTIC_PROFILE_ID,
        "sha256": semantic_profile_sha256(),
    }


def semantic_profile_v1_identity() -> dict[str, object]:
    """Return the historical identity used by pre-H0.1b artifacts."""

    return {
        "format": SEMANTIC_PROFILE_FORMAT,
        "v": SEMANTIC_PROFILE_V1_VERSION,
        "id": SEMANTIC_PROFILE_V1_ID,
        "sha256": semantic_profile_v1_sha256(),
    }


def semantic_profile_registration(digest: str) -> dict[str, object]:
    """Resolve an immutable profile registration by semantic digest.

    Registry lookup deliberately performs only artifact-integrity checks.  It
    does not compare a historical profile with today's kernel implementation;
    that comparison is a separate diagnostic and must not reinterpret old
    result records when a future profile becomes active.
    """

    if type(digest) is not str:
        raise SemanticProfileError("semantic profile digest must be text")
    if digest == SEMANTIC_PROFILE_V1_SHA256:
        if semantic_profile_v1_sha256() != digest:  # pragma: no cover - pinned
            raise SemanticProfileError("semantic profile v1 registry drifted")
        return {
            "certificate_representation": (
                "python-dataclass-repr-with-cut-v2"
            ),
            "format": SEMANTIC_PROFILE_FORMAT,
            "id": SEMANTIC_PROFILE_V1_ID,
            "logic": "intuitionistic",
            "result_schema_sha256": None,
            "result_schema_version": None,
            "sha256": SEMANTIC_PROFILE_V1_SHA256,
            "theorem_canonicalizer": "canonical-profile-theorem-v1",
            "v": SEMANTIC_PROFILE_V1_VERSION,
        }
    if digest == SEMANTIC_PROFILE_V2_SHA256:
        if semantic_profile_v2_sha256() != digest:  # pragma: no cover - pinned
            raise SemanticProfileError("semantic profile v2 registry drifted")
        return {
            "certificate_representation": "peano-lab-v2",
            "format": SEMANTIC_PROFILE_FORMAT,
            "id": SEMANTIC_PROFILE_ID,
            "logic": "intuitionistic",
            "result_schema_sha256": _PROFILE_V2_RESULT_SCHEMA_SHA256,
            "result_schema_version": _PROFILE_V2_RESULT_SCHEMA_VERSION,
            "sha256": SEMANTIC_PROFILE_V2_SHA256,
            "theorem_canonicalizer": "canonical-profile-theorem-v2",
            "v": SEMANTIC_PROFILE_VERSION,
        }
    raise SemanticProfileError("semantic profile sha256 is not registered")


def validate_semantic_profile_alignment(profile: object) -> None:
    """Diagnose whether one exact registered profile matches the live kernel."""

    if type(profile) is not dict:
        raise SemanticProfileError("semantic profile must be one exact JSON object")
    digest = hashlib.sha256(_canonical_json_bytes(profile)).hexdigest()
    registration = semantic_profile_registration(digest)
    if registration["v"] == SEMANTIC_PROFILE_V1_VERSION:
        checked = validate_semantic_profile_v1(profile)
    else:
        checked = validate_semantic_profile(profile)
    _validate_kernel_alignment(checked)


def _well_scoped_term(term: object, depth: int) -> bool:
    if type(term) is Var:
        return type(term.index) is int and 0 <= term.index < depth
    if type(term) is Zero:
        return True
    if type(term) is Succ:
        return _well_scoped_term(term.term, depth)
    if type(term) in (Add, Mul):
        return _well_scoped_term(term.left, depth) and _well_scoped_term(
            term.right, depth
        )
    return False


def well_scoped_formula(formula: object, depth: int = 0) -> bool:
    """Decide structural de Bruijn scope for one core formula."""

    if type(depth) is not int or depth < 0:
        raise ValueError("scope depth must be a non-negative integer")
    if type(formula) is Eq:
        return _well_scoped_term(formula.left, depth) and _well_scoped_term(
            formula.right, depth
        )
    if type(formula) is Bot:
        return True
    if type(formula) in (Imp, And, Or):
        return well_scoped_formula(formula.left, depth) and well_scoped_formula(
            formula.right, depth
        )
    if type(formula) in (Forall, Exists):
        return well_scoped_formula(formula.body, depth + 1)
    return False


def _canonical_profile_theorem_v1_v2(source: str) -> str:
    """Frozen theorem admission shared by semantic profiles v1 and v2."""

    try:
        return _canonicalize_profile_theorem_v1_v2(source)
    except FrozenProfileTheoremError as exc:
        raise SemanticProfileError(str(exc)) from None


def _canonical_profile_formula_v1_v2(formula: Formula) -> str:
    """Frozen formula printer shared by semantic profiles v1 and v2."""

    try:
        return _canonicalize_profile_formula_v1_v2(formula)
    except FrozenProfileTheoremError as exc:
        raise SemanticProfileError(str(exc)) from None


def canonical_registered_profile_theorem(digest: str, source: str) -> str:
    """Canonicalize with the frozen grammar registered for ``digest``."""

    registration = semantic_profile_registration(digest)
    canonicalizer = registration["theorem_canonicalizer"]
    if canonicalizer == "canonical-profile-theorem-v1":
        return _canonical_profile_theorem_v1_v2(source)
    if canonicalizer == "canonical-profile-theorem-v2":
        return _canonical_profile_theorem_v1_v2(source)
    raise SemanticProfileError("registered theorem canonicalizer is unsupported")


def canonical_registered_profile_formula(digest: str, formula: Formula) -> str:
    """Print a kernel formula with the frozen printer registered for ``digest``."""

    registration = semantic_profile_registration(digest)
    canonicalizer = registration["theorem_canonicalizer"]
    if canonicalizer == "canonical-profile-theorem-v1":
        return _canonical_profile_formula_v1_v2(formula)
    if canonicalizer == "canonical-profile-theorem-v2":
        return _canonical_profile_formula_v1_v2(formula)
    raise SemanticProfileError("registered theorem canonicalizer is unsupported")


def canonical_profile_theorem(source: str) -> str:
    """Canonicalize with the currently active semantic profile."""

    return canonical_registered_profile_theorem(
        semantic_profile_sha256(),
        source,
    )


def evidence_kind(*, proved: bool, kernel_checked: bool) -> EvidenceKind:
    """Map a final positive judgment or all other outcomes to safe evidence."""

    if type(proved) is not bool or type(kernel_checked) is not bool:
        raise TypeError("evidence flags must be Booleans")
    if proved:
        if not kernel_checked:
            raise SemanticProfileError(
                "proved evidence requires an independent kernel acceptance"
            )
        return "proved"
    if kernel_checked:
        raise SemanticProfileError(
            "kernel acceptance cannot be published as unknown evidence"
        )
    return "unknown"


__all__ = [
    "EvidenceKind",
    "MAX_SEMANTIC_PROFILE_BYTES",
    "SEMANTIC_PROFILE_FORMAT",
    "SEMANTIC_PROFILE_ID",
    "SEMANTIC_PROFILE_PATH",
    "SEMANTIC_PROFILE_V1_ID",
    "SEMANTIC_PROFILE_V1_DOCUMENT_SHA256",
    "SEMANTIC_PROFILE_V1_PATH",
    "SEMANTIC_PROFILE_V1_SHA256",
    "SEMANTIC_PROFILE_V1_VERSION",
    "SEMANTIC_PROFILE_V2_DOCUMENT_SHA256",
    "SEMANTIC_PROFILE_V2_SHA256",
    "SEMANTIC_PROFILE_VERSION",
    "SemanticProfileError",
    "canonical_profile_theorem",
    "canonical_registered_profile_formula",
    "canonical_registered_profile_theorem",
    "evidence_kind",
    "semantic_profile",
    "semantic_profile_identity",
    "semantic_profile_sha256",
    "semantic_profile_registration",
    "semantic_profile_v1",
    "semantic_profile_v1_identity",
    "semantic_profile_v1_sha256",
    "semantic_profile_v2",
    "semantic_profile_v2_sha256",
    "validate_semantic_profile_alignment",
    "validate_semantic_profile",
    "validate_semantic_profile_v1",
    "well_scoped_formula",
]
