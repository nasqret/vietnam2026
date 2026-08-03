"""Exact-byte tests for the inert Cut-aware kernel artifact encoder."""

from __future__ import annotations

import builtins

import pytest

import peano_lab.kernel.artifact_codec as artifact_codec
from peano_lab.kernel.artifact_codec import (
    ArtifactLimitError,
    encode_artifact,
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
    encode_term,
)
from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or
from peano_lab.kernel.proofs import (
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
)
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero


ZERO = Zero()
ATOM = Eq(ZERO, ZERO)
REFL = EqRefl(ZERO)


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        (Var(12), b'["var",12]'),
        (ZERO, b'["zero"]'),
        (Succ(Var(2)), b'["succ",["var",2]]'),
        (Add(ZERO, Var(1)), b'["add",["zero"],["var",1]]'),
        (Mul(Var(3), ZERO), b'["mul",["var",3],["zero"]]'),
    ],
)
def test_every_term_constructor_has_exact_canonical_bytes(
    term: object, expected: bytes
) -> None:
    assert encode_term(term) == expected


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        (ATOM, b'["eq",["zero"],["zero"]]'),
        (Bot(), b'["bot"]'),
        (Imp(ATOM, Bot()), b'["imp",["eq",["zero"],["zero"]],["bot"]]'),
        (And(ATOM, Bot()), b'["and",["eq",["zero"],["zero"]],["bot"]]'),
        (Or(ATOM, Bot()), b'["or",["eq",["zero"],["zero"]],["bot"]]'),
        (Forall(ATOM), b'["forall",["eq",["zero"],["zero"]]]'),
        (Exists(ATOM), b'["exists",["eq",["zero"],["zero"]]]'),
    ],
)
def test_every_formula_constructor_has_exact_canonical_bytes(
    formula: object, expected: bytes
) -> None:
    assert encode_formula(formula) == expected


@pytest.mark.parametrize(
    ("proof", "expected"),
    [
        (Hyp(3), b'["hyp",3]'),
        (ImpIntro(Hyp(0)), b'["imp_intro",["hyp",0]]'),
        (ImpElim(Hyp(0), Hyp(1)), b'["imp_elim",["hyp",0],["hyp",1]]'),
        (
            Cut(ATOM, ATOM, REFL, Hyp(0)),
            b'["cut",["eq",["zero"],["zero"]],["eq",["zero"],["zero"]],'
            b'["eq_refl",["zero"]],["hyp",0]]',
        ),
        (AndIntro(Hyp(0), Hyp(1)), b'["and_intro",["hyp",0],["hyp",1]]'),
        (AndElimL(Hyp(0)), b'["and_elim_l",["hyp",0]]'),
        (AndElimR(Hyp(0)), b'["and_elim_r",["hyp",0]]'),
        (OrIntroL(Hyp(0)), b'["or_intro_l",["hyp",0]]'),
        (OrIntroR(Hyp(0)), b'["or_intro_r",["hyp",0]]'),
        (
            OrElim(Hyp(0), Hyp(1), Hyp(2)),
            b'["or_elim",["hyp",0],["hyp",1],["hyp",2]]',
        ),
        (BotElim(Hyp(0)), b'["bot_elim",["hyp",0]]'),
        (ForallIntro(Hyp(0)), b'["forall_intro",["hyp",0]]'),
        (
            ForallElim(Hyp(0), Var(2)),
            b'["forall_elim",["hyp",0],["var",2]]',
        ),
        (
            ExistsIntro(Var(2), Hyp(0)),
            b'["exists_intro",["var",2],["hyp",0]]',
        ),
        (ExistsElim(Hyp(0), Hyp(1)), b'["exists_elim",["hyp",0],["hyp",1]]'),
        (REFL, b'["eq_refl",["zero"]]'),
        (EqSym(Hyp(0)), b'["eq_sym",["hyp",0]]'),
        (EqTrans(Hyp(0), Hyp(1)), b'["eq_trans",["hyp",0],["hyp",1]]'),
        (CongS(Hyp(0)), b'["cong_s",["hyp",0]]'),
        (CongAdd(Hyp(0), Hyp(1)), b'["cong_add",["hyp",0],["hyp",1]]'),
        (CongMul(Hyp(0), Hyp(1)), b'["cong_mul",["hyp",0],["hyp",1]]'),
        (
            EqSubst(ATOM, Hyp(0), Hyp(1)),
            b'["eq_subst",["eq",["zero"],["zero"]],["hyp",0],["hyp",1]]',
        ),
        (DNE(ATOM), b'["dne",["eq",["zero"],["zero"]]]'),
        (Axiom("PA6"), b'["axiom","PA6"]'),
        (
            Ind(ATOM, Hyp(0), Hyp(1)),
            b'["ind",["eq",["zero"],["zero"]],["hyp",0],["hyp",1]]',
        ),
    ],
)
def test_every_proof_constructor_has_exact_canonical_bytes(
    proof: object, expected: bytes
) -> None:
    assert encode_proof(proof) == expected


@pytest.mark.parametrize("number", range(1, 7))
def test_every_axiom_name_is_encoded_without_a_generic_string_path(number: int) -> None:
    name = f"PA{number}"
    assert encode_proof(Axiom(name)) == f'["axiom","{name}"]'.encode("ascii")


def test_exact_lean_forall_refl_fixture() -> None:
    target = Forall(Eq(Var(0), Var(0)))
    proof = ForallIntro(EqRefl(Var(0)))
    expected = (
        b'["peano-lab-v2",32,["forall",["eq",["var",0],["var",0]]],'
        b'["forall_intro",["eq_refl",["var",0]]]]\n'
    )
    assert encode_artifact(32, target, proof) == expected


def test_exact_lean_cut_refl_fixture() -> None:
    target = Eq(ZERO, ZERO)
    proof = Cut(target, target, EqRefl(ZERO), Hyp(0))
    expected = (
        b'["peano-lab-v2",64,["eq",["zero"],["zero"]],'
        b'["cut",["eq",["zero"],["zero"]],["eq",["zero"],["zero"]],'
        b'["eq_refl",["zero"]],["hyp",0]]]\n'
    )
    assert encode_artifact(64, target, proof) == expected


def test_bounded_artifact_encoder_includes_terminal_lf_in_exact_limit() -> None:
    artifact = encode_artifact(1, ATOM, REFL)

    assert (
        encode_artifact_bounded(1, ATOM, REFL, max_bytes=len(artifact))
        == artifact
    )
    with pytest.raises(ArtifactLimitError, match="canonical artifact exceeds"):
        encode_artifact_bounded(1, ATOM, REFL, max_bytes=len(artifact) - 1)


def test_bounded_encoder_rejects_huge_naturals_before_decimal_chunk_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    huge = 1 << 100_000
    real_divmod = builtins.divmod

    def guarded_divmod(value: int, divisor: int) -> tuple[int, int]:
        assert value.bit_length() < 1_000, "huge natural reached the chunk allocator"
        return real_divmod(value, divisor)

    monkeypatch.setattr(artifact_codec, "divmod", guarded_divmod, raising=False)
    cases = (
        (huge, ATOM, REFL),
        (1, Eq(Var(huge), ZERO), REFL),
        (1, ATOM, Hyp(huge)),
    )
    for fuel, target, proof in cases:
        with pytest.raises(ArtifactLimitError, match="canonical artifact exceeds"):
            encode_artifact_bounded(fuel, target, proof, max_bytes=64)


@pytest.mark.parametrize("limit", [None, 0, -1, True, 1.5])
def test_bounded_encoder_accepts_none_or_rejects_non_positive_exact_ints(
    limit: object,
) -> None:
    if limit is None:
        assert encode_artifact_bounded(1, ATOM, REFL, max_bytes=None).endswith(b"\n")
        return
    with pytest.raises(ValueError, match="positive integer"):
        encode_artifact_bounded(1, ATOM, REFL, max_bytes=limit)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_fuel", [True, False, -1, 1.0, "1", None])
def test_artifact_fuel_must_be_an_exact_nonnegative_integer(bad_fuel: object) -> None:
    with pytest.raises(ValueError, match="artifact fuel must be a non-negative integer"):
        encode_artifact(bad_fuel, ATOM, REFL)


@pytest.mark.parametrize("bad_index", [True, -1, 2.0, "2", None])
def test_variable_and_hypothesis_indices_fail_closed(bad_index: object) -> None:
    with pytest.raises(ValueError, match="variable index"):
        encode_term(Var(bad_index))
    with pytest.raises(ValueError, match="hypothesis index"):
        encode_proof(Hyp(bad_index))


def test_arbitrary_lean_naturals_ignore_cpython_decimal_digit_limit() -> None:
    huge = 10**5000
    decimal = b"1" + b"0" * 5000
    assert encode_term(Var(huge)) == b'["var",' + decimal + b"]"
    assert encode_artifact(huge, ATOM, REFL).startswith(
        b'["peano-lab-v2",' + decimal + b","
    )


def test_subclassed_syntax_is_rejected_at_every_layer() -> None:
    class EvilZero(Zero):
        pass

    class EvilEq(Eq):
        pass

    class EvilRefl(EqRefl):
        pass

    with pytest.raises(TypeError, match="exact Peano Lab term"):
        encode_term(EvilZero())
    with pytest.raises(TypeError, match="exact Peano Lab formula"):
        encode_formula(EvilEq(ZERO, ZERO))
    with pytest.raises(TypeError, match="exact Peano Lab proof"):
        encode_proof(EvilRefl(ZERO))
    with pytest.raises(TypeError, match="exact Peano Lab formula"):
        encode_artifact(1, EvilEq(ZERO, ZERO), REFL)


def test_adversarial_metaclass_equality_cannot_bypass_exact_type_checks() -> None:
    class EqualMeta(type):
        def __eq__(cls, other: object) -> bool:
            return True

        def __hash__(cls) -> int:
            return 0

    class EvilZero(Zero, metaclass=EqualMeta):
        pass

    class EvilBot(Bot, metaclass=EqualMeta):
        pass

    class EvilHyp(Hyp, metaclass=EqualMeta):
        pass

    with pytest.raises(TypeError, match="exact Peano Lab term"):
        encode_term(EvilZero())
    with pytest.raises(TypeError, match="exact Peano Lab formula"):
        encode_formula(EvilBot())
    with pytest.raises(TypeError, match="exact Peano Lab proof"):
        encode_proof(EvilHyp(0))
    with pytest.raises(TypeError, match="exact Peano Lab proof"):
        encode_artifact(1, ATOM, EvilHyp(0))


def test_nested_malformed_and_runtime_mutated_nodes_are_rejected() -> None:
    with pytest.raises(TypeError, match="exact Peano Lab term"):
        encode_term(Succ(object()))
    with pytest.raises(TypeError, match="exact Peano Lab formula"):
        encode_formula(Imp(ATOM, object()))
    with pytest.raises(TypeError, match="exact Peano Lab proof"):
        encode_proof(ImpIntro(object()))

    mutated = EqRefl(ZERO)
    object.__setattr__(mutated, "t", object())
    with pytest.raises(TypeError, match="exact Peano Lab term"):
        encode_proof(mutated)


def test_missing_fields_and_cycles_fail_closed() -> None:
    missing = object.__new__(Succ)
    with pytest.raises(TypeError, match="malformed Peano Lab syntax"):
        encode_term(missing)

    cyclic = object.__new__(Succ)
    object.__setattr__(cyclic, "term", cyclic)
    with pytest.raises(ValueError, match="cyclic Peano Lab syntax"):
        encode_term(cyclic)


def test_axiom_names_are_an_exact_closed_enumeration() -> None:
    class Text(str):
        pass

    for bad_name in ("PA0", "PA7", "pa1", Text("PA1"), 1, None):
        with pytest.raises(ValueError, match="exactly PA1 through PA6"):
            encode_proof(Axiom(bad_name))


def test_encoding_is_inert_and_does_not_claim_the_proof_matches_the_target() -> None:
    false_target = Eq(ZERO, Succ(ZERO))
    encoded = encode_artifact(0, false_target, EqRefl(ZERO))
    assert encoded == (
        b'["peano-lab-v2",0,["eq",["zero"],["succ",["zero"]]],'
        b'["eq_refl",["zero"]]]\n'
    )
    assert type(encoded) is bytes
    assert encoded.endswith(b"\n") and not encoded.endswith(b"\n\n")


def test_exported_format_label_cannot_mutate_the_wire_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(artifact_codec, "FORMAT_TAG", "attacker-controlled")
    assert encode_artifact(1, ATOM, REFL).startswith(b'["peano-lab-v2",1,')
