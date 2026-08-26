"""Small native fixtures only: no full Alpha loading, replay or acceptance run."""

from dataclasses import fields, replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel import formulas as f, proofs as p, terms as t  # noqa: E402
from peano_lab.library.theorems import CheckedTheorem, TheoremSpec  # noqa: E402
from training.peano_hydra.epoch import EpochTheorem, HydraEpoch  # noqa: E402
from training.peano_hydra import cold_replay as cold  # noqa: E402


def _hash(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _theorem(name="fixture_refl", *, index=0, statement="0 = 0", dependencies=(), membership="stable"):
    script = ("refl",)
    return EpochTheorem(name, statement, sha256(statement.encode()).hexdigest(), script,
                        sha256(b"refl\n").hexdigest(), tuple(dependencies), membership, index)


def _synthetic_epoch():
    """A declaration-count fixture, explicitly NOT real library proof evidence."""
    rows = []
    for index in range(cold.ALPHA_V25_COUNT):
        dependencies = [f"fixture_{prior}" for prior in range(max(0, index - 3), index)]
        if 4 <= index <= 402:
            dependencies.insert(0, f"fixture_{index - 4}")
        rows.append(_theorem(f"fixture_{index}", index=index, dependencies=dependencies,
                             membership="stable" if index < 432 else "alpha_only"))
    projection = [{"name": row.name, "dependencies": list(row.dependencies)} for row in rows]
    return HydraEpoch(version="v25", edition_identity_sha256=cold.ALPHA_V25_IDENTITY,
        alpha_catalog_sha256="a" * 64, stable_catalog_sha256="b" * 64,
        definition_artifact_sha256="c" * 64, campaign_artifact_sha256="d" * 64,
        theorem_dag_sha256=_hash(projection), reviewed_definition_dag_sha256="e" * 64,
        milestone_dag_sha256="f" * 64, theorems=tuple(rows), definitions=(), stable_count=432,
        theorem_edge_count=6633, definition_edge_count=0, milestone_count=0, milestone_edge_count=0,
        blueprint_definition_count=0, blueprint_definition_edge_count=0, notation_edge_count=0)


def test_plan_preserves_full_order_exact_routes_and_does_not_replay(monkeypatch):
    monkeypatch.setattr(cold, "_runtime", lambda: pytest.fail("planning cannot load or replay native Alpha"))
    epoch = _synthetic_epoch()
    plan = cold.build_cold_replay_plan(epoch)
    assert plan["target_count"] == len(plan["targets"]) == 2080
    assert plan["passes"] == 2
    assert plan["fresh_process_per_target_required"] is True
    assert plan["parent_resource_guard_required"] is True
    assert plan["parallel_workers"] == 1
    assert plan["proofs_checked"] == 0 and plan["status"] == "planned"
    assert plan["all_scripts_regenerated"] is False
    assert plan["research_claim_eligible"] is False
    for index, (row, original) in enumerate(zip(plan["targets"], epoch.theorems)):
        assert row["enrollment_index"] == index
        assert row["statement"] == original.statement
        assert row["script"] == list(original.script)
        assert row["dependencies"] == list(original.dependencies)
    assert plan["targets_sha256"] == _hash(plan["targets"])
    unsigned = dict(plan)
    assert unsigned.pop("plan_sha256") == _hash(unsigned)


@pytest.mark.parametrize("mutation", ("subset", "order", "forward_dependency", "version", "identity", "stable", "edges", "dag_digest"))
def test_plan_cannot_relabel_partial_or_changed_inventory_as_full(mutation):
    epoch = _synthetic_epoch()
    if mutation == "subset":
        epoch = replace(epoch, theorems=epoch.theorems[:-1])
    elif mutation == "order":
        epoch = replace(epoch, theorems=tuple(reversed(epoch.theorems)))
    elif mutation == "forward_dependency":
        epoch = replace(epoch, theorems=(replace(epoch.theorems[0], dependencies=("fixture_1",)), *epoch.theorems[1:]))
    elif mutation == "version":
        epoch = replace(epoch, version="v24")
    elif mutation == "identity":
        epoch = replace(epoch, edition_identity_sha256="0" * 64)
    elif mutation == "stable":
        epoch = replace(epoch, stable_count=431)
    elif mutation == "edges":
        epoch = replace(epoch, theorem_edge_count=6632)
    elif mutation == "dag_digest":
        epoch = replace(epoch, theorem_dag_sha256="0" * 64)
    with pytest.raises(cold.ColdReplayError):
        cold.build_cold_replay_plan(epoch)


def test_explicit_batches_preserve_one_full_order_without_claiming_cold_each_target():
    plan = cold.build_cold_replay_plan(_synthetic_epoch(), batch_size=16)
    assert plan["batch_size"] == 16 and plan["batch_count"] == 130
    assert plan["batches"] == [list(range(start, start + 16)) for start in range(0, 2080, 16)]
    assert plan["batches_sha256"] == _hash(plan["batches"])
    assert plan["cache_scope"] == "one-frozen-batch"
    assert plan["fresh_process_per_batch_required"] is True
    assert plan["fresh_process_per_target_required"] is False
    assert plan["passes"] == 2 and plan["proofs_checked"] == 0
    for invalid in (0, 17, True):
        with pytest.raises(cold.ColdReplayError, match="batch size"):
            cold.build_cold_replay_plan(_synthetic_epoch(), batch_size=invalid)


def test_complete_constructor_layout_and_exact_field_order():
    layouts = cold._layouts()
    expected = {getattr(p, name) for name in p.__all__ if name not in {"Proof", "DNE"}}
    assert {kind for kind, (domain, _, _) in layouts.items() if domain == "proof"} == expected
    for kind, (_, _, layout) in layouts.items():
        assert tuple(field for field, _ in layout) == tuple(field.name for field in fields(kind))


def test_fingerprint_has_independent_tagged_constructor_serialization():
    zero_digest = _hash([cold.CERTIFICATE_SCHEMA, "term", "zero", []])
    expected = _hash([cold.CERTIFICATE_SCHEMA, "proof", "eq_refl", [["t", "term", zero_digest]]])
    result = cold.fingerprint_certificate(p.EqRefl(t.Zero()))
    assert result == {"schema": cold.CERTIFICATE_SCHEMA, "sha256": expected, "proof_nodes": 1,
        "proof_depth": 1, "annotation_nodes": 1, "envelope_depth": 2,
        "proof_objects": 1, "proof_edges": 0, "syntax_objects": 2,
        "sharing_independent_digest": True, "dne_objects": 0}


def test_fingerprint_is_structural_not_python_identity_or_sharing():
    atom = p.EqRefl(t.Zero())
    shared = cold.fingerprint_certificate(p.AndIntro(atom, atom))
    expanded = cold.fingerprint_certificate(p.AndIntro(p.EqRefl(t.Zero()), p.EqRefl(t.Zero())))
    assert shared["sha256"] == expanded["sha256"]
    assert shared["proof_nodes"] == expanded["proof_nodes"] == 3
    assert shared["annotation_nodes"] == expanded["annotation_nodes"] == 2
    assert shared["proof_objects"] == 2 and expanded["proof_objects"] == 3
    assert shared["syntax_objects"] < expanded["syntax_objects"]


def test_every_proof_field_contributes_to_fingerprint():
    eq = f.Eq(t.Zero(), t.Zero())
    one = f.Eq(t.Succ(t.Zero()), t.Succ(t.Zero()))
    original = p.Cut(eq, eq, p.EqRefl(t.Zero()), p.Hyp(0))
    changes = (replace(original, proposition=one), replace(original, conclusion=one),
               replace(original, lemma=p.EqSym(p.EqRefl(t.Zero()))), replace(original, body=p.Hyp(1)))
    fingerprints = {cold.fingerprint_certificate(item)["sha256"] for item in (original, *changes)}
    assert len(fingerprints) == 5
    assert cold.fingerprint_certificate(p.Axiom("PA1"))["sha256"] != cold.fingerprint_certificate(p.Axiom("PA2"))["sha256"]


@pytest.mark.parametrize("bad", (p.DNE(f.Bot()), p.Hyp(True), p.Hyp(-1), p.Hyp(2**31),
                                p.Axiom("new_axiom"), p.EqRefl(4), p.ImpIntro(f.Bot()), object()))
def test_fingerprint_rejects_classical_malformed_and_foreign_syntax(bad):
    with pytest.raises(cold.ColdReplayError):
        cold.fingerprint_certificate(bad)


def test_fingerprint_rejects_subclass_and_cycles_without_recursion():
    class PretendRefl(p.EqRefl):
        pass
    with pytest.raises(cold.ColdReplayError):
        cold.fingerprint_certificate(PretendRefl(t.Zero()))
    cyclic = p.ImpIntro(p.Hyp(0))
    object.__setattr__(cyclic, "body", cyclic)
    with pytest.raises(cold.ColdReplayError, match="cyclic"):
        cold.fingerprint_certificate(cyclic)


@pytest.mark.parametrize("field", ("max_proof_objects", "max_syntax_objects", "max_proof_nodes",
                                   "max_annotation_nodes", "max_proof_depth", "max_envelope_depth"))
def test_fingerprint_limits_fail_closed(field):
    value = p.AndIntro(p.EqRefl(t.Zero()), p.EqRefl(t.Zero()))
    limits = replace(cold.CertificateLimits(), **{field: 1})
    with pytest.raises(cold.ColdReplayError):
        cold.fingerprint_certificate(value, limits=limits)
    with pytest.raises(cold.ColdReplayError):
        replace(limits, **{field: True})


def test_exponentially_referenced_dag_is_rejected_without_expanding_it():
    proof = p.EqRefl(t.Zero())
    for _ in range(20):
        proof = p.AndIntro(proof, proof)
    with pytest.raises(cold.ColdReplayError, match="structural"):
        cold.fingerprint_certificate(proof)


@pytest.fixture
def native_fixture(monkeypatch):
    theorem = _theorem()
    spec = TheoremSpec(theorem.name, theorem.statement, theorem.dependencies, theorem.script, "test-only")
    checked = CheckedTheorem(spec, f.Eq(t.Zero(), t.Zero()), p.EqRefl(t.Zero()), 1)
    entry = SimpleNamespace(spec=spec, checked_use=True, membership=SimpleNamespace(value="stable"))
    calls = []
    def replay(name, *, edition):
        calls.append((name, edition))
        return runtime.result
    runtime = SimpleNamespace(ALPHA_V25_IDENTITY_SHA256=cold.ALPHA_V25_IDENTITY,
                              ALPHA_EDITION=SimpleNamespace(entries=(entry,) * 2080),
                              replay=replay, result=checked)
    monkeypatch.setattr(cold, "_runtime", lambda: runtime)
    return theorem, runtime, calls


def _replay(record, **kwargs):
    return cold.replay_cold_target(record, epoch_sha256="a" * 64,
                                  edition_identity_sha256=cold.ALPHA_V25_IDENTITY, **kwargs)


def test_replay_uses_public_provider_then_real_original_goal_kernel(native_fixture, monkeypatch):
    import peano_lab.kernel.checker as checker
    theorem, runtime, calls = native_fixture
    target = cold.cold_target_record(theorem)
    actual_check = checker.check
    kernel_calls = []
    def tracked(context, proof, formula):
        kernel_calls.append((context, proof, formula))
        return actual_check(context, proof, formula)
    monkeypatch.setattr(checker, "check", tracked)
    receipt = _replay(target)
    assert calls == [(theorem.name, "alpha")]
    assert kernel_calls == [((), runtime.result.certificate, runtime.result.formula)]
    assert receipt["kernel_checked"] is True
    assert receipt["status"] == "checked"
    assert receipt["target_sha256"] == target["target_sha256"]
    assert receipt["model_calls"] == receipt["solver_calls"] == 0
    assert receipt["lean_companion_invoked"] is False
    assert receipt["runtime_internal_kernel_calls"] is None
    unsigned = dict(receipt)
    assert unsigned.pop("receipt_sha256") == _hash(unsigned)


@pytest.mark.parametrize("mutation", ("false_certificate", "wrong_formula", "wrong_spec", "wrong_size", "untyped_result"))
def test_replay_never_trusts_public_checked_result_without_exact_recheck(native_fixture, mutation):
    theorem, runtime, _ = native_fixture
    checked = runtime.result
    if mutation == "false_certificate":
        runtime.result = replace(checked, certificate=p.Hyp(0))
    elif mutation == "wrong_formula":
        runtime.result = replace(checked, formula=f.Eq(t.Succ(t.Zero()), t.Succ(t.Zero())))
    elif mutation == "wrong_spec":
        runtime.result = replace(checked, spec=replace(checked.spec, name="different"))
    elif mutation == "wrong_size":
        runtime.result = replace(checked, proof_nodes=2)
    elif mutation == "untyped_result":
        runtime.result = SimpleNamespace(kernel_checked=True)
    with pytest.raises(cold.ColdReplayError):
        _replay(cold.cold_target_record(theorem))


def test_resealed_changed_script_is_rejected_before_public_replay(native_fixture):
    theorem, _, calls = native_fixture
    changed = replace(theorem, script=("norm_num",), script_sha256=sha256(b"norm_num\n").hexdigest())
    with pytest.raises(cold.ColdReplayError, match="declaration"):
        _replay(cold.cold_target_record(changed))
    assert calls == []


def test_bad_target_bounds_and_identity_fail_before_loading_alpha(monkeypatch):
    target = cold.cold_target_record(_theorem())
    monkeypatch.setattr(cold, "_runtime", lambda: pytest.fail("Alpha loaded before validating input"))
    for key, value in (("statement", "x" * (cold.MAX_STATEMENT_BYTES + 1)),
                       ("script", ["refl"] * (cold.MAX_SCRIPT_COMMANDS + 1)),
                       ("enrollment_index", True), ("statement_sha256", "0" * 64)):
        with pytest.raises(cold.ColdReplayError):
            _replay({**target, key: value})
    with pytest.raises(cold.ColdReplayError):
        cold.replay_cold_target(target, epoch_sha256="a" * 64, edition_identity_sha256="0" * 64)


def test_target_route_is_detached_and_can_exceed_small_dev_source_profile():
    theorem = _theorem(statement="forall n. n = n" + " " * 5000)
    target = cold.cold_target_record(theorem)
    assert len(target["statement"]) > 4096
    target["script"].append("not_original")
    assert theorem.script == ("refl",)
    with pytest.raises(cold.ColdReplayError, match="digest"):
        cold._target_checked(target)


def test_adapter_import_and_small_fingerprints_need_no_model_or_lean():
    before = set(sys.modules)
    cold.fingerprint_certificate(p.EqRefl(t.Zero()))
    assert not ({"torch", "transformers", "peft", "peano_lab.library.editions_v25"} & (set(sys.modules) - before))
