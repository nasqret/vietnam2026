"""Original-kernel positives, independent arithmetic and hostile mutations."""
import pytest

from sqrt2_power_binary_certificates import (
    BinaryCertificateError, BinaryLimits, binary_term, binary_power_term,
    prove_add, prove_mul, prove_binary_equation, p10_difference_equation,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import CongMul, Cut, EqRefl, EqTrans, Hyp
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library.proof_bundle import check_encoded_proof_bundle


@pytest.fixture(scope="module")
def basis():
    from sqrt2_power_native import Basis
    return Basis()


def _interpret(term):
    if type(term) is Zero:
        return 0
    if type(term) is Succ:
        return 1 + _interpret(term.term)
    if type(term) is Add:
        return _interpret(term.left) + _interpret(term.right)
    if type(term) is Mul:
        return _interpret(term.left) * _interpret(term.right)
    raise AssertionError("not closed arithmetic")


@pytest.mark.parametrize("n", (0, 1, 2, 3, 127, 129, 256, 2**88))
def test_binary_syntax_has_exact_value(n):
    # Other campaign tests may deliberately import the full registry. This
    # function must not introduce or replace it, independent of test order.
    before = __import__('sys').modules.get("peano_lab.library.theorems")
    term = binary_term(n)
    assert _interpret(term) == n
    assert __import__('sys').modules.get("peano_lab.library.theorems") is before


@pytest.mark.parametrize("operation,a,b", (("add", 2, 3), ("add", 127, 129), ("mul", 17, 19)))
def test_small_actual_closed_certificates(operation, a, b, basis, monkeypatch):
    import peano_lab.engine.decide as unary
    def forbidden(*_a, **_k):
        raise AssertionError("binary proof called unary normalization")
    monkeypatch.setattr(unary, "_normalization_proof", forbidden)
    monkeypatch.setattr(unary, "_bounded_normalization_proof", forbidden)
    result = (prove_add if operation == "add" else prove_mul)(a, b, basis)
    expected = a + b if operation == "add" else a * b
    assert result.value == expected
    assert result.formula.right == binary_term(expected)
    assert check((), result.certificate, result.formula)
    receipt = check_encoded_proof_bundle(result.payload)
    assert receipt.target == result.formula and receipt.kernel_calls == 1
    assert result.proof_depth <= 256 and len(result.payload.encode()) <= 8*1024**2
    altered = Eq(result.formula.left, binary_term(expected + 1))
    assert not check((), result.certificate, altered)
    assert not check((), EqRefl(result.formula.right), result.formula)


@pytest.mark.parametrize("bad", (-1, True, 2**128))
def test_bad_numerals_fail_closed(bad):
    with pytest.raises(BinaryCertificateError):
        binary_term(bad)


def test_false_open_and_overbudget_targets_need_no_basis():
    for equation in (Eq(binary_term(2), binary_term(3)), Eq(Var(0), Zero())):
        with pytest.raises(BinaryCertificateError):
            prove_binary_equation(equation, None)
    with pytest.raises(BinaryCertificateError):
        prove_binary_equation(Eq(binary_term(256), binary_term(256)), None,
                              limits=BinaryLimits(max_value_bits=8))
    with pytest.raises(BinaryCertificateError):
        BinaryLimits(max_value_bits=129)


def test_construction_budget_precedes_copying(monkeypatch):
    import sqrt2_power_binary_certificates as binary
    def forbidden(*_a, **_k):
        raise AssertionError("overbudget proof reached a copying traversal")
    monkeypatch.setattr(binary, "_shift_hypotheses", forbidden)
    builder = binary._Builder(BinaryLimits(max_proof_nodes=1))
    goal = Eq(Zero(), Zero())
    with pytest.raises(BinaryCertificateError, match="copy-work budget"):
        builder.share(goal, EqRefl(Zero()), goal, lambda ref: ref)


def test_serialization_preflight_counts_repeated_term_occurrences():
    import sqrt2_power_binary_certificates as binary
    shared = Mul(binary_term(127), binary_term(129))
    target = Eq(shared, shared)
    with pytest.raises(BinaryCertificateError, match="serialization budget"):
        binary._serialization_preflight(EqRefl(shared), target,
                                        BinaryLimits(max_payload_bytes=1024))


def test_identical_squaring_operands_use_one_cut_hypothesis(monkeypatch):
    import sqrt2_power_binary_certificates as binary
    # Equal syntax need not be the same Python object.
    left = Add(binary_term(1), binary_term(1))
    right = Add(binary_term(1), binary_term(1))
    term = Mul(left, right)
    limits = BinaryLimits()
    values, _ = binary._values(Eq(term, binary_term(4)), limits)
    builder = binary._Builder(limits)
    original = builder.normalize
    visits = []
    def recording(current, values):
        visits.append(current)
        return original(current, values)
    monkeypatch.setattr(builder, "normalize", recording)
    proof = builder.normalize(term, values)
    assert sum(current == left for current in visits) == 1
    assert type(proof) is Cut and type(proof.body) is EqTrans
    assert proof.body.first == CongMul(Hyp(0), Hyp(0))


def test_multiplication_orders_by_fewer_set_bits_without_swap_cycle():
    import sqrt2_power_binary_certificates as binary
    builder = binary._Builder(BinaryLimits())
    proof = builder.mul(2, 7)
    assert type(proof) is Cut
    assert proof.proposition == Eq(Mul(binary_term(7), binary_term(2)), binary_term(14))
    assert type(proof.body) is EqTrans and proof.body.second == Hyp(0)
    assert ("mul", 7, 2) in builder.memo and ("mul", 2, 7) in builder.memo


def test_power_inputs_are_actual_products_and_p10_false_mutation():
    assert _interpret(binary_power_term(3, 11)) == 177147
    equation = p10_difference_equation()
    assert _interpret(equation.left) == _interpret(equation.right) == 2**88
    assert _interpret(equation.left.right) > 0
    with pytest.raises(BinaryCertificateError, match="false"):
        p10_difference_equation(85)


@pytest.mark.xfail(strict=True, raises=BinaryCertificateError,
    reason="P10 remains unresolved: copy-work cap rejects the large certificate; not a proof")
def test_p10_actual_closed_certificate(basis):
    result = prove_binary_equation(p10_difference_equation(), basis)
    assert check((), result.certificate, result.formula)
    assert result.value == 2**88
    assert not check((), result.certificate, Eq(result.formula.left, binary_term(2**85)))
