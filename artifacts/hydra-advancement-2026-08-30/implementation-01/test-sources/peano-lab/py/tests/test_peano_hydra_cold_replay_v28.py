"""Actual v28 metadata plus tiny native fixtures; no library campaign or Lean."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from training.peano_hydra import cold_replay as legacy
from training.peano_hydra import cold_replay_v28 as cold
from training.peano_hydra.epoch import EpochTheorem, freeze_epoch
from peano_lab.kernel import formulas as f, proofs as p, terms as t
from peano_lab.library.theorems import CheckedTheorem, TheoremSpec


@pytest.fixture(scope="module")
def epoch():
    return freeze_epoch(ROOT)


def test_full_actual_inventory_is_compact_pinned_and_does_not_replay(epoch, monkeypatch):
    monkeypatch.setattr(cold, "_runtime", lambda: pytest.fail("metadata cannot load public replay"))
    plan = cold.build_cold_replay_plan(epoch, selected_names=cold.HOTSPOT_NAMES)
    assert plan["epoch_sha256"] == cold.ALPHA_V28_EPOCH
    assert plan["full_target_records_sha256"] == cold.ALPHA_V28_TARGETS
    assert len(plan["targets"]) == plan["target_count"] == 2764
    assert len(cold._canonical(plan)) < cold.MAX_PLAN_BYTES
    assert [row["enrollment_index"] for row in plan["targets"]] == list(range(2764))
    assert sum(row["membership"] == "stable" for row in plan["targets"]) == 432
    assert set(plan["selected_targets"]) == {"1108", "1940"}
    assert len(plan["outside_replay_profile"]) == 17
    assert all(row["reasons"] == ["statement-byte-limit"] for row in plan["outside_replay_profile"])
    assert {row["name"] for row in plan["outside_replay_profile"]} <= {row["name"] for row in plan["targets"]}
    assert max(row["statement_bytes"] for row in plan["targets"]) == 254812
    assert plan["full_execution_envelope"] is None
    assert plan["full_execution_authorized"] is False
    assert plan["proofs_checked"] == 0
    assert cold.MAX_PLAN_BYTES == legacy.MAX_PLAN_BYTES
    assert cold.MAX_STATEMENT_BYTES == legacy.MAX_STATEMENT_BYTES


@pytest.mark.parametrize("change", ["v25", "epoch", "subset", "order", "script", "statement", "dependencies"])
def test_complete_epoch_cannot_be_resealed_around_altered_targets(epoch, change):
    if change == "v25":
        changed = replace(epoch, version="v25")
    elif change == "epoch":
        changed = replace(epoch, campaign_artifact_sha256="0" * 64)
    elif change == "subset":
        changed = replace(epoch, theorems=epoch.theorems[:-1])
    elif change == "order":
        changed = replace(epoch, theorems=tuple(reversed(epoch.theorems)))
    else:
        row = epoch.theorems[0]
        if change == "script":
            row = replace(row, script=("refl",), script_sha256=sha256(b"refl\n").hexdigest())
        elif change == "statement":
            row = replace(row, statement="0 = 0", statement_sha256=sha256(b"0 = 0").hexdigest())
        else:
            row = replace(row, dependencies=(epoch.theorems[1].name,))
        changed = replace(epoch, theorems=(row, *epoch.theorems[1:]))
    with pytest.raises(cold.ColdReplayError):
        cold.build_cold_replay_plan(changed)


def test_oversize_target_stays_in_inventory_but_cannot_enter_worker(epoch, monkeypatch):
    monkeypatch.setattr(cold, "_runtime", lambda: pytest.fail("outside-profile target reached native runtime"))
    name = "rectangular_matrix_rank_integer_invariant"
    with pytest.raises(cold.ColdReplayError, match="byte reservation"):
        cold.build_cold_replay_plan(epoch, selected_names=(name,))
    with pytest.raises(cold.ColdReplayError, match="byte reservation"):
        cold.cold_target_record(epoch.theorem(name))


@pytest.mark.parametrize("batch", [0, 17, True])
def test_batch_caps_not_increased(epoch, batch):
    with pytest.raises(cold.ColdReplayError, match="batch size"):
        cold.build_cold_replay_plan(epoch, batch_size=batch)


@pytest.fixture
def native_fixture(monkeypatch):
    theorem = EpochTheorem("fixture_refl", "0 = 0", sha256(b"0 = 0").hexdigest(), ("refl",),
                           sha256(b"refl\n").hexdigest(), (), "stable", 0)
    spec = TheoremSpec(theorem.name, theorem.statement, (), theorem.script, "synthetic fixture")
    checked = CheckedTheorem(spec, f.Eq(t.Zero(), t.Zero()), p.EqRefl(t.Zero()), 1)
    entry = SimpleNamespace(spec=spec, checked_use=True, membership=SimpleNamespace(value="stable"))
    runtime = SimpleNamespace(ALPHA_V28_IDENTITY_SHA256=cold.ALPHA_V28_IDENTITY,
                              ALPHA_EDITION=SimpleNamespace(entries=(entry,) * 2764), result=checked)
    calls = []
    def replay(name, *, edition):
        calls.append((name, edition))
        return runtime.result
    runtime.replay = replay
    monkeypatch.setattr(cold, "_runtime", lambda: runtime)
    return theorem, runtime, calls


def _replay(target, epoch=cold.ALPHA_V28_EPOCH):
    return cold.replay_cold_target(target, epoch_sha256=epoch, edition_identity_sha256=cold.ALPHA_V28_IDENTITY)


def test_v28_replay_rechecks_real_original_goal_and_certificate(native_fixture):
    theorem, runtime, calls = native_fixture
    receipt = _replay(cold.cold_target_record(theorem))
    assert calls == [(theorem.name, "alpha")]
    assert receipt["schema"] == cold.COLD_REPLAY_SCHEMA
    assert receipt["epoch_sha256"] == cold.ALPHA_V28_EPOCH
    assert receipt["kernel_checked"] is True
    assert receipt["independent_recheck_calls"] == 1
    assert receipt["all_scripts_regenerated"] is False
    assert receipt["research_claim_eligible"] is False


@pytest.mark.parametrize("change", ["v25", "false_certificate", "wrong_goal", "wrong_spec", "wrong_size"])
def test_public_provider_label_is_not_accepted_as_proof(native_fixture, change):
    theorem, runtime, calls = native_fixture
    if change == "v25":
        epoch = "a96223a021edc556ed7620a87b4c00e5817ba169af4a1db093fa7a81847e082e"
    else:
        epoch = cold.ALPHA_V28_EPOCH
        replacements = {
            "false_certificate": {"certificate": p.Hyp(0)},
            "wrong_goal": {"formula": f.Eq(t.Succ(t.Zero()), t.Zero())},
            "wrong_spec": {"spec": replace(runtime.result.spec, name="other")},
            "wrong_size": {"proof_nodes": 2},
        }
        runtime.result = replace(runtime.result, **replacements[change])
    with pytest.raises(cold.ColdReplayError):
        _replay(cold.cold_target_record(theorem), epoch)
    if change == "v25":
        assert calls == []
