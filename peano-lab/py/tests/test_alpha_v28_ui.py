"""Current lower-layer UI routing never upgrades inspection into proof authority."""

from __future__ import annotations

import driver
from hashlib import sha256
import pytest

from peano_lab.library.alpha_enrollment_v28 import ROOT_STATEMENT_SHA256
from peano_lab.library import lean_proof_strand, theorems
from peano_lab.ui import data_library


@pytest.fixture(scope="module")
def alpha():
    # Deliberately no fallback to v27: unsealed v28 must fail closed.
    from peano_lab.library import editions_v28

    return editions_v28


def _forbid_proof_loading(monkeypatch,alpha):
    def forbidden(*_args,**_kwargs):
        raise AssertionError("a lower-layer metadata view loaded an actual proof")

    for edition,provider in (
        (alpha,"_checked_lower_layer_bundle"),
        (alpha.v27,"_checked_second_wave_bundle"),
        (alpha.v27.v26,"_checked_first_wave_bundle"),
    ):
        monkeypatch.setattr(edition,"replay",forbidden)
        monkeypatch.setattr(edition,provider,forbidden)
    monkeypatch.setattr(alpha,"checked_lower_layer_bundle",forbidden)
    monkeypatch.setattr(data_library,"replay",forbidden)
    monkeypatch.setattr(data_library,"export_checked_theorem",forbidden)
    monkeypatch.setattr(lean_proof_strand,"build_proof_strand",forbidden)


@pytest.mark.parametrize("name",tuple(ROOT_STATEMENT_SHA256))
def test_lower_layer_principal_cards_are_current_opt_in_and_replay_free(monkeypatch,alpha,name):
    _forbid_proof_loading(monkeypatch,alpha)
    item=alpha.entry(name,edition="alpha")
    assert item is not None and item.checked_use
    assert name in alpha.FRONTIER_NEW_NAMES
    assert alpha.entry(name,edition="stable") is None
    assert theorems.get(name) is None

    output=driver.LabSession().run(f"pa lib alpha {name}")

    assert f"{name} — Alpha v28 theorem evidence" in output
    assert "Release membership: alpha_only" in output
    assert "Checked-use authority: YES" in output
    assert "This evidence card does not itself replay a proof." in output
    assert "Independent empty-context kernel check: PASS" not in output


@pytest.mark.parametrize("name",tuple(ROOT_STATEMENT_SHA256))
@pytest.mark.parametrize("command",("pa proof alpha","pa lean alpha","pa lean alpha exact"))
def test_lower_layer_browser_previews_keep_limits_and_verification_disclosures(monkeypatch,alpha,name,command):
    _forbid_proof_loading(monkeypatch,alpha)

    output=driver.LabSession().run(f"{command} {name}")

    assert name in output
    assert "Release edition: Alpha v28." in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Checked-use authority: YES." in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "--edition alpha" in output and "--verify" in output
    assert len(output.encode("utf-8"))<=15*1024
    if command.startswith("pa proof"):
        assert "Release membership: alpha_only." in output
        assert "Fresh Peano proof replay: NOT RUN" in output
    else:
        assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output


@pytest.mark.parametrize("name",tuple(ROOT_STATEMENT_SHA256))
def test_lower_layer_exact_lean_strand_planning_uses_no_closed_proof_artifact(monkeypatch,alpha,name):
    _forbid_proof_loading(monkeypatch,alpha)

    plan=lean_proof_strand.plan_proof_strand(name,edition="alpha")

    assert plan.edition_version=="v28"
    assert plan.root==name
    assert plan.root_node.evidence=="alpha_closed"
    assert plan.root_node.membership=="alpha_only"
    assert plan.root_node.source_path.startswith("peano-lab/py/peano_lab/library/")
    assert sha256(plan.root_node.statement.encode()).hexdigest()==ROOT_STATEMENT_SHA256[name]
    assert plan.node_count>=1


def test_lower_layer_seal_guard_does_not_block_unchanged_stable(alpha,monkeypatch):
    monkeypatch.setattr(alpha,"EXPECTED_ALPHA_V28_COUNT",0)
    with pytest.raises(lean_proof_strand.ProofStrandError,match="not sealed"):
        lean_proof_strand._edition_view("alpha")
    stable,version=lean_proof_strand._edition_view("stable")
    assert version=="stable" and len(stable.entries)==432
    assert driver.LabSession().run("pa lib zero_add").startswith("zero_add — checked theorem")
