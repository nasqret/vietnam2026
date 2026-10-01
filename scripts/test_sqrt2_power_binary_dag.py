"""Exact-target, original-kernel, independent-model, and adverse DAG checks.

Root owns all execution. Exclude test_p10_full_original_target for the initial
small probe; do not turn its resource failure into a passing/xfail proof claim.
"""
from dataclasses import fields, replace
import sys

import pytest

import sqrt2_power_binary_dag as dag
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Exists, Imp
from peano_lab.kernel.proofs import Cut, EqRefl, ExistsIntro, ImpIntro, Proof
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library.proof_bundle import (
    ProofBundleError, check_proof_bundle, check_encoded_proof_bundle,
)


@pytest.fixture(scope="module")
def basis():
    from sqrt2_power_native import Basis
    return Basis()


def _interpret(term):
    if type(term) is Zero:
        return 0
    if type(term) is Succ:
        return _interpret(term.term) + 1
    if type(term) is Add:
        return _interpret(term.left) + _interpret(term.right)
    if type(term) is Mul:
        return _interpret(term.left) * _interpret(term.right)
    raise AssertionError("non-closed arithmetic term")


def _curried(bundle, node):
    result = node.target
    for dependency in reversed(node.dependencies):
        result = Imp(bundle.nodes[dependency].target, result)
    return result


def _proof_nodes(body):
    pending = [body]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(child for field in fields(node)
                       if isinstance(child := getattr(node, field.name), Proof))


def test_frozen_p10_original_syntax_and_independent_integer_model():
    target, subleaf, witness = dag.frozen_p10_targets()
    assert type(target) is Exists and type(subleaf) is Eq
    assert dag.formula_sha256(target) == dag.P10_TARGET_SHA256
    assert dag.formula_sha256(subleaf) == dag.P10_SUBLEAF_SHA256
    assert _interpret(subleaf.left.left) == 2**55 * 3**11 * 7**5
    assert _interpret(subleaf.right) == 2**88
    assert _interpret(witness) == 2**88 - 2**55 * 3**11 * 7**5 > 0
    assert _interpret(subleaf.left) == _interpret(subleaf.right)
    assert 2**55 * 3**11 * 7**5 > 2**85
    # A host-equal binary-normal-form rewrite is NOT the frozen source AST.
    alternate = Eq(Add(subleaf.left.left, dag.binary_term(_interpret(witness))), subleaf.right)
    assert alternate != subleaf
    assert dag.formula_sha256(alternate) != dag.P10_SUBLEAF_SHA256
    dag._values(subleaf, dag.BinaryDAGLimits())


def test_v2_basis_pins_without_theorem_registry_import():
    assert dag.verify_basis_sources() == dag.SOURCE_PINS
    assert len(dag.LAW_PINS) == 7
    assert "peano_lab.library.theorems" not in sys.modules


@pytest.mark.parametrize("n", (0, 1, 2, 3, 127, 129, 256, 2**88))
def test_binary_terms_have_exact_independent_values(n):
    assert _interpret(dag.binary_term(n)) == n


@pytest.mark.parametrize("operation,a,b", (
    ("add", 2, 3), ("add", 127, 129), ("mul", 17, 19),
    ("add", 0, 0), ("mul", 0, 31), ("mul", 31, 0),
    ("mul", 1, 19), ("mul", 2, 7), ("mul", 19, 1),
))
def test_small_original_kernel_bundles(operation, a, b, basis, monkeypatch):
    import peano_lab.engine.decide as unary
    def forbidden(*_a, **_k):
        raise AssertionError("DAG arithmetic invoked unary normalization")
    monkeypatch.setattr(unary, "_normalization_proof", forbidden)
    monkeypatch.setattr(unary, "_bounded_normalization_proof", forbidden)
    constructor = Add if operation == "add" else Mul
    expected = a + b if operation == "add" else a * b
    equation = Eq(constructor(dag.binary_term(a), dag.binary_term(b)), dag.binary_term(expected))
    result = dag.prove_binary_equation(equation, basis)
    assert result.target == equation == result.receipt.target
    assert result.receipt.kernel_calls == len(result.bundle.nodes)
    assert result.receipt.total_body_nodes <= 200000
    assert result.max_proof_depth <= 256
    assert len(result.payload.encode()) <= 8 * 1024**2
    assert len(result.bundle.nodes) <= 4096
    assert check_proof_bundle(result.bundle, equation).target == equation
    assert check_encoded_proof_bundle(result.payload).target == equation
    for node in result.bundle.nodes:
        assert all(dependency < node.node_id for dependency in node.dependencies)
        assert len(node.dependencies) == len(set(node.dependencies))
        if type(node.target) is Eq:
            assert not any(type(body) is Cut for body in _proof_nodes(node.body))
    wrong = Eq(equation.left, dag.binary_term(expected + 1))
    with pytest.raises(ProofBundleError, match="exact caller target"):
        check_proof_bundle(result.bundle, wrong)


def test_bad_body_and_dependencies_are_rejected_by_original_kernel(basis):
    equation = Eq(Mul(dag.binary_term(17), dag.binary_term(19)), dag.binary_term(323))
    result = dag.prove_binary_equation(equation, basis)
    root = result.bundle.nodes[result.bundle.root]
    assert not check((), EqRefl(Zero()), _curried(result.bundle, root))
    bad_root = replace(root, body=EqRefl(Zero()))
    bad_bundle = replace(result.bundle, nodes=tuple(
        bad_root if node.node_id == root.node_id else node for node in result.bundle.nodes))
    with pytest.raises(ProofBundleError, match="kernel rejected"):
        check_proof_bundle(bad_bundle, equation)
    # Removing an actual dependency changes the implication context: the
    # original body must fail even before any bundle reachability diagnostic.
    dependent = next(node for node in reversed(result.bundle.nodes) if node.dependencies)
    omitted = replace(dependent, dependencies=dependent.dependencies[1:])
    assert not check((), omitted.body, _curried(result.bundle, omitted))
    dangling = replace(root, dependencies=(len(result.bundle.nodes),))
    with pytest.raises(ProofBundleError, match="dangling"):
        check_proof_bundle(replace(result.bundle, nodes=tuple(
            dangling if node.node_id == root.node_id else node for node in result.bundle.nodes)), equation)
    circular = replace(root, dependencies=(root.node_id,))
    with pytest.raises(ProofBundleError, match="cycle"):
        check_proof_bundle(replace(result.bundle, nodes=tuple(
            circular if node.node_id == root.node_id else node for node in result.bundle.nodes)), equation)


def test_false_open_and_overbit_targets_do_not_load_basis(monkeypatch):
    def forbidden(*_a, **_k):
        raise AssertionError("invalid arithmetic reached Basis")
    monkeypatch.setattr(dag, "_basis", forbidden)
    for target in (Eq(dag.binary_term(2), dag.binary_term(3)), Eq(Var(0), Zero())):
        with pytest.raises(dag.BinaryDAGError):
            dag.prove_binary_equation(target)
    with pytest.raises(dag.BinaryDAGError):
        dag.prove_binary_equation(Eq(dag.binary_term(256), dag.binary_term(256)),
                                  limits=dag.BinaryDAGLimits(max_value_bits=8))


@pytest.mark.parametrize("bad", (-1, True, 2**128))
def test_bad_binary_numerals(bad):
    with pytest.raises(dag.BinaryDAGError):
        dag.binary_term(bad)


@pytest.mark.parametrize("field", tuple(field.name for field in fields(dag.BinaryDAGLimits)))
def test_resource_limits_cannot_be_widened(field):
    maximum = getattr(dag.BinaryDAGLimits(), field)
    with pytest.raises(dag.BinaryDAGError, match="widened"):
        dag.BinaryDAGLimits(**{field: maximum + 1})


def test_original_target_and_basis_source_mutations_fail_closed(monkeypatch):
    import sqrt2_power_pilot_instances as instances
    original = instances.p10_instance
    def changed_source():
        record = original()
        record["sources"][0]["formula"] = "exists delta. (0 + delta) = 0"
        return record
    monkeypatch.setattr(instances, "p10_instance", changed_source)
    with pytest.raises(dag.BinaryDAGError, match="AST pin"):
        dag.frozen_p10_targets()
    monkeypatch.setitem(dag.SOURCE_PINS, "scripts/sqrt2_power_native.py", "0" * 64)
    with pytest.raises(dag.BinaryDAGError, match="v2 pins"):
        dag.verify_basis_sources()


def test_topology_and_node_budget_fail_before_body_construction():
    builder = dag._Builder(None, dag.BinaryDAGLimits(max_nodes=1))
    target = Eq(Zero(), Zero())
    def forbidden(_):
        raise AssertionError("invalid topology reached body construction")
    with pytest.raises(dag.BinaryDAGError, match="non-topological"):
        builder.emit(target, (0,), forbidden)
    builder.emit(target, (), lambda _: EqRefl(Zero()))
    with pytest.raises(dag.BinaryDAGError, match="node budget"):
        builder.emit(Eq(dag.binary_term(1), dag.binary_term(1)), (), forbidden)


def test_p10_full_original_target(basis):
    """This is a real positive obligation; resource failure is NOT a pass."""
    result = dag.prove_p10(basis)
    target, subleaf, witness = dag.frozen_p10_targets()
    assert result.target == target == result.receipt.target
    assert result.target_ast_sha256 == dag.P10_TARGET_SHA256
    assert result.subleaf_node is not None
    assert result.bundle.nodes[result.subleaf_node].target == subleaf
    assert dag.formula_sha256(subleaf) == dag.P10_SUBLEAF_SHA256
    root = result.bundle.nodes[result.bundle.root]
    assert root.dependencies == (result.subleaf_node,)
    assert type(root.body) is ImpIntro and type(root.body.body) is ExistsIntro
    assert root.body.body.term == witness
    assert check_proof_bundle(result.bundle, target).target == target
    assert result.receipt.kernel_calls == len(result.bundle.nodes) <= 4096
    assert result.receipt.total_body_nodes <= 200000
    assert len(result.payload.encode()) <= 8 * 1024**2
    assert result.max_proof_depth <= 256
    assert "peano_lab.library.theorems" not in sys.modules
