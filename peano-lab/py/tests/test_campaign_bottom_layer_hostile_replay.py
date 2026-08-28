"""Untrusted compiler/interner returns cannot become HA proof authority."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.proofs import EqRefl, Hyp
from peano_lab.kernel.terms import Succ, Zero
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec, _closed_formula


@pytest.fixture
def tiny_checked_checkpoint(monkeypatch):
    """Tiny test-only syntax; the actual original checker is never replaced."""
    parent = TheoremSpec("hostile_parent", "0=0", (), ("refl",), "Test-only true parent.")
    row = TheoremSpec("hostile_child", "0=0", (parent.name,), ("exact hostile_parent",), "Test-only child.")
    monkeypatch.setattr(closure, "parent_snapshot", lambda: closure.ParentSnapshot((parent,), ()))
    result = closure.assemble_bottom_layer_bundle((row,), report=lambda _: None)
    return (row,), result


def _replay(checkpoint):
    frontier, result = checkpoint
    return closure.replay_bottom_layer_theorem(frontier, frontier[0].name, result.bundle, result.target)


@pytest.mark.parametrize("certificate", (Hyp(0), EqRefl(Succ(Zero()))))
def test_forged_compiler_output_is_rejected_by_the_actual_empty_context_kernel(tiny_checked_checkpoint, monkeypatch, certificate):
    assert not check((), certificate, _closed_formula("0=0"))
    observed = []

    def forged_compiler(layered, formula, *, limits):
        assert limits is closure.DEFAULT_LAYERED_REPLAY_LIMITS
        observed.append(formula)
        return SimpleNamespace(certificate=certificate, proof_nodes=1)

    monkeypatch.setattr(closure, "compile_gaussian_factorization_replay", forged_compiler)
    with pytest.raises(closure.BottomLayerClosureError, match="original HA kernel/resource policy"):
        _replay(tiny_checked_checkpoint)
    assert observed == [_closed_formula("0=0")]


def test_compiler_resource_refusal_remains_fail_closed(tiny_checked_checkpoint, monkeypatch):
    monkeypatch.setattr(closure, "compile_gaussian_factorization_replay", lambda *_args, **_kwargs: None)
    with pytest.raises(closure.BottomLayerClosureError, match="kernel/resource policy"):
        _replay(tiny_checked_checkpoint)


@pytest.mark.parametrize("mutation", ("id", "target", "premises", "body", "missing", "extra", "reordered", "refused"))
def test_forged_interner_output_cannot_change_graph_or_bodies(tiny_checked_checkpoint, monkeypatch, mutation):
    original = closure.intern_layered_replay_bodies

    def forged_interner(layered, formula, *, limits):
        assert limits is closure.DEFAULT_LAYERED_REPLAY_LIMITS
        actual = original(layered, formula, limits=limits)
        assert actual is not None and len(actual.nodes) == 2
        nodes = list(actual.nodes)
        if mutation == "refused":
            return None
        if mutation == "id":
            nodes[0] = replace(nodes[0], node_id=7)
        elif mutation == "target":
            nodes[0] = replace(nodes[0], target=_closed_formula("0=1"))
        elif mutation == "premises":
            nodes[0] = replace(nodes[0], dependencies=(1,))
        elif mutation == "body":
            nodes[0] = replace(nodes[0], body=Hyp(0))
        elif mutation == "missing":
            nodes.pop()
        elif mutation == "extra":
            nodes.append(nodes[-1])
        else:
            nodes.reverse()
        return replace(actual, nodes=tuple(nodes))

    monkeypatch.setattr(closure, "intern_layered_replay_bodies", forged_interner)
    monkeypatch.setattr(closure, "compile_gaussian_factorization_replay",
                        lambda *_args, **_kwargs: pytest.fail("forged interner reached compiler"))
    with pytest.raises(ValueError):
        _replay(tiny_checked_checkpoint)


def test_valid_generic_compiler_still_produces_an_original_ha_certificate(tiny_checked_checkpoint):
    theorem = _replay(tiny_checked_checkpoint)
    assert theorem.formula == _closed_formula("0=0")
    assert theorem.proof_nodes > 0
    assert check((), theorem.certificate, theorem.formula)
