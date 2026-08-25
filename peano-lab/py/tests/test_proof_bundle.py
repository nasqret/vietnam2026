"""Self-contained, one-pass constructive proof bundles and canonical codecs."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess

import pytest

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
import peano_lab.library.proof_bundle as bundles


ZERO = Zero()
ONE = Succ(ZERO)
P = Eq(ZERO, ZERO)
Q = Eq(ONE, ONE)
LEAN_BUNDLE_VERIFIER = (
    Path(__file__).resolve().parents[4]
    / "peano-lab-lean"
    / ".lake"
    / "build"
    / "bin"
    / "peano_lab_bundle_verify"
)


def _bundle() -> bundles.ProofBundle:
    return bundles.ProofBundle(
        nodes=(
            bundles.BundleNode(10, P, (), EqRefl(ZERO)),
            bundles.BundleNode(
                30,
                And(P, P),
                (10,),
                ImpIntro(AndIntro(Hyp(0), Hyp(0))),
            ),
        ),
        root=30,
    )


@pytest.mark.parametrize(
    "term",
    (ZERO, Var(2), Succ(Var(0)), Add(Var(0), ONE), Mul(ONE, Var(3))),
)
def test_full_term_codec_roundtrips_exact_kernel_constructors(term) -> None:
    assert bundles.decode_term(bundles.encode_term(term)) == term


@pytest.mark.parametrize(
    "formula",
    (
        P,
        Bot(),
        And(P, Q),
        Or(P, Q),
        Imp(P, Q),
        Forall(Eq(Var(0), Var(0))),
        Exists(Eq(Var(0), ZERO)),
    ),
)
def test_full_formula_codec_roundtrips_exact_kernel_constructors(formula) -> None:
    assert bundles.decode_formula(bundles.encode_formula(formula)) == formula


@pytest.mark.parametrize(
    "proof",
    (
        Hyp(0),
        ImpIntro(Hyp(0)),
        ImpElim(Hyp(0), Hyp(1)),
        Cut(P, Q, EqRefl(ZERO), EqRefl(ONE)),
        AndIntro(Hyp(0), Hyp(1)),
        AndElimL(Hyp(0)),
        AndElimR(Hyp(0)),
        OrIntroL(Hyp(0)),
        OrIntroR(Hyp(0)),
        OrElim(Hyp(0), Hyp(1), Hyp(2)),
        BotElim(Hyp(0)),
        ForallIntro(Hyp(0)),
        ForallElim(Hyp(0), ZERO),
        ExistsIntro(ZERO, Hyp(0)),
        ExistsElim(Hyp(0), Hyp(1)),
        EqRefl(ZERO),
        EqSym(Hyp(0)),
        EqTrans(Hyp(0), Hyp(1)),
        CongS(Hyp(0)),
        CongAdd(Hyp(0), Hyp(1)),
        CongMul(Hyp(0), Hyp(1)),
        EqSubst(Eq(Var(0), ZERO), Hyp(0), Hyp(1)),
        DNE(P),
        Axiom("PA1"),
        Ind(Eq(Var(0), Var(0)), EqRefl(ZERO), Hyp(0)),
    ),
)
def test_full_proof_codec_roundtrips_every_inert_kernel_constructor(proof) -> None:
    assert bundles.decode_proof(bundles.encode_proof(proof)) == proof


def test_each_dependency_curried_body_is_checked_once_in_the_empty_context(
    monkeypatch,
) -> None:
    calls = []
    original = bundles.kernel_checker.check

    def checked(context, proof, target):
        calls.append((context, proof, target))
        return original(context, proof, target)

    monkeypatch.setattr(bundles.kernel_checker, "check", checked)

    receipt = bundles.check_proof_bundle(_bundle(), And(P, P))

    assert receipt.topological_order == (10, 30)
    assert receipt.kernel_calls == receipt.node_count == 2
    assert receipt.dependency_edges == 1
    assert len(calls) == 2
    assert all(context == () for context, _, _ in calls)
    assert calls[0][2] == P
    assert calls[1][2] == Imp(P, And(P, P))


def test_canonical_bundle_roundtrip_renumbers_dense_local_ids() -> None:
    payload = bundles.encode_proof_bundle(_bundle(), And(P, P))

    decoded, target = bundles.decode_proof_bundle(payload)
    receipt = bundles.check_encoded_proof_bundle(payload)

    assert payload.endswith("\n")
    assert json.loads(payload)[0] == bundles.PROOF_BUNDLE_FORMAT
    assert tuple(node.node_id for node in decoded.nodes) == (0, 1)
    assert decoded.root == 1
    assert target == And(P, P)
    assert receipt.topological_order == (0, 1)
    assert receipt.kernel_calls == 2
    assert bundles.encode_proof_bundle(decoded, target) == payload


def test_topological_canonicalization_is_input_order_independent() -> None:
    original = _bundle()
    reversed_bundle = replace(original, nodes=tuple(reversed(original.nodes)))

    assert bundles.encode_proof_bundle(
        original, And(P, P)
    ) == bundles.encode_proof_bundle(reversed_bundle, And(P, P))
    assert bundles.check_proof_bundle(
        reversed_bundle, And(P, P)
    ).topological_order == (10, 30)


def test_wrong_root_statement_and_mutated_body_fail_closed() -> None:
    original = _bundle()
    leaf, root = original.nodes

    with pytest.raises(bundles.ProofBundleError, match="root"):
        bundles.check_proof_bundle(original, P)
    with pytest.raises(bundles.ProofBundleError, match="rejected"):
        bundles.check_proof_bundle(
            replace(original, nodes=(replace(leaf, body=EqRefl(ONE)), root)),
            And(P, P),
        )


@pytest.mark.parametrize(
    "mutated,match",
    (
        (
            bundles.ProofBundle(
                (
                    bundles.BundleNode(0, P, (1,), ImpIntro(Hyp(0))),
                    bundles.BundleNode(1, P, (0,), ImpIntro(Hyp(0))),
                ),
                0,
            ),
            "cycle",
        ),
        (
            bundles.ProofBundle(
                (bundles.BundleNode(0, P, (99,), ImpIntro(Hyp(0))),), 0
            ),
            "dangling",
        ),
        (
            bundles.ProofBundle(
                (
                    bundles.BundleNode(0, P, (), EqRefl(ZERO)),
                    bundles.BundleNode(0, P, (), EqRefl(ZERO)),
                ),
                0,
            ),
            "duplicate local",
        ),
        (
            bundles.ProofBundle(
                (
                    bundles.BundleNode(0, P, (), EqRefl(ZERO)),
                    bundles.BundleNode(
                        1,
                        P,
                        (0, 0),
                        ImpIntro(ImpIntro(Hyp(0))),
                    ),
                ),
                1,
            ),
            "duplicate local dependency",
        ),
        (
            bundles.ProofBundle(
                (
                    bundles.BundleNode(0, P, (), EqRefl(ZERO)),
                    bundles.BundleNode(1, Q, (), EqRefl(ONE)),
                ),
                0,
            ),
            "unreachable",
        ),
    ),
)
def test_cycles_missing_edges_duplicate_edges_and_unreachable_nodes_are_rejected(
    mutated: bundles.ProofBundle,
    match: str,
) -> None:
    with pytest.raises(bundles.ProofBundleError, match=match):
        bundles.check_proof_bundle(mutated, P)


def test_open_targets_and_classical_dne_are_rejected() -> None:
    opened = Eq(Var(0), Var(0))
    open_bundle = bundles.ProofBundle(
        (bundles.BundleNode(0, opened, (), EqRefl(Var(0))),),
        0,
    )
    dne_target = Imp(Imp(Imp(P, Bot()), Bot()), P)
    classical = bundles.ProofBundle(
        (bundles.BundleNode(0, dne_target, (), DNE(P)),),
        0,
    )

    with pytest.raises(bundles.ProofBundleError, match="closed"):
        bundles.check_proof_bundle(open_bundle, opened)
    with pytest.raises(bundles.ProofBundleError, match="rejected"):
        bundles.check_proof_bundle(classical, dne_target)


@pytest.mark.parametrize(
    "decode,value",
    (
        (bundles.decode_term, ["var", True]),
        (bundles.decode_term, ["zero", 1]),
        (bundles.decode_formula, ["eq", ["zero"]]),
        (bundles.decode_formula, ["forall", ["zero"]]),
        (bundles.decode_proof, ["hyp", -1]),
        (bundles.decode_proof, ["axiom", "PA7"]),
        (bundles.decode_proof, ["cut", ["bot"], ["bot"], ["eq_refl", ["zero"]]]),
        (bundles.decode_proof, ["trusted_hash", "deadbeef"]),
    ),
)
def test_noncanonical_wrong_arity_and_external_authority_tags_are_rejected(
    decode,
    value: object,
) -> None:
    with pytest.raises(bundles.ProofBundleError):
        decode(value)


def test_canonical_decoder_rejects_spacing_forward_edges_and_zero_fuel() -> None:
    payload = bundles.encode_proof_bundle(_bundle(), And(P, P))
    record = json.loads(payload)
    with pytest.raises(bundles.ProofBundleError, match="not canonical"):
        bundles.decode_proof_bundle(json.dumps(record) + "\n")

    forward = json.loads(payload)
    forward[3][0][2] = [1]
    with pytest.raises(bundles.ProofBundleError, match="backward"):
        bundles.decode_proof_bundle(
            json.dumps(forward, separators=(",", ":")) + "\n"
        )

    no_fuel = json.loads(payload)
    no_fuel[3][0][0] = 0
    with pytest.raises(bundles.ProofBundleError, match="fuel"):
        bundles.decode_proof_bundle(
            json.dumps(no_fuel, separators=(",", ":")) + "\n"
        )


@pytest.mark.parametrize("insufficient_fuel", (1, 23))
def test_explicit_fuel_must_cover_conservative_independent_checker_allowance(
    insufficient_fuel: int,
) -> None:
    original = _bundle()
    leaf, root = original.nodes
    insufficient = replace(
        original,
        nodes=(replace(leaf, fuel=insufficient_fuel), root),
    )

    with pytest.raises(bundles.ProofBundleError, match="conservative checker"):
        bundles.check_proof_bundle(insufficient, And(P, P))
    with pytest.raises(bundles.ProofBundleError, match="conservative checker"):
        bundles.encode_proof_bundle(insufficient, And(P, P))

    encoded = json.loads(bundles.encode_proof_bundle(original, And(P, P)))
    encoded[3][0][0] = insufficient_fuel
    with pytest.raises(bundles.ProofBundleError, match="conservative checker"):
        bundles.decode_proof_bundle(
            json.dumps(encoded, separators=(",", ":")) + "\n"
        )


def test_fail_closed_resource_limits_are_checked_before_kernel_invocations(
    monkeypatch,
) -> None:
    called = False

    def forbidden(*args):
        nonlocal called
        called = True
        raise AssertionError("kernel must not run after invalid resource preflight")

    monkeypatch.setattr(bundles.kernel_checker, "check", forbidden)
    with pytest.raises(bundles.ProofBundleError, match="node count"):
        bundles.check_proof_bundle(
            _bundle(),
            And(P, P),
            limits=replace(bundles.DEFAULT_BUNDLE_LIMITS, max_nodes=1),
        )
    assert not called


@pytest.mark.skipif(
    not LEAN_BUNDLE_VERIFIER.is_file(),
    reason="independent sibling Lean bundle verifier is not installed",
)
def test_python_canonical_bundle_is_accepted_by_independent_lean_process(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "shared.json"
    artifact.write_text(
        bundles.encode_proof_bundle(_bundle(), And(P, P)),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(LEAN_BUNDLE_VERIFIER), str(artifact)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("ACCEPT\t")
    assert "nodes=2" in result.stdout


@pytest.mark.skipif(
    not LEAN_BUNDLE_VERIFIER.is_file(),
    reason="independent sibling Lean bundle verifier is not installed",
)
def test_independent_lean_process_rejects_mutated_validly_encoded_body(
    tmp_path: Path,
) -> None:
    record = json.loads(bundles.encode_proof_bundle(_bundle(), And(P, P)))
    record[3][0][3] = ["eq_refl", ["succ", ["zero"]]]
    payload = json.dumps(record, separators=(",", ":")) + "\n"
    artifact = tmp_path / "mutated.json"
    artifact.write_text(payload, encoding="utf-8")

    with pytest.raises(bundles.ProofBundleError, match="rejected"):
        bundles.check_encoded_proof_bundle(payload)
    result = subprocess.run(
        [str(LEAN_BUNDLE_VERIFIER), str(artifact)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout.startswith("REJECT\t")


@pytest.mark.skipif(
    not LEAN_BUNDLE_VERIFIER.is_file(),
    reason="independent sibling Lean bundle verifier is not installed",
)
def test_python_and_independent_lean_both_reject_insufficient_checker_fuel(
    tmp_path: Path,
) -> None:
    record = json.loads(bundles.encode_proof_bundle(_bundle(), And(P, P)))
    record[3][0][0] = 1
    payload = json.dumps(record, separators=(",", ":")) + "\n"
    artifact = tmp_path / "insufficient-fuel.json"
    artifact.write_text(payload, encoding="utf-8")

    with pytest.raises(bundles.ProofBundleError, match="conservative checker"):
        bundles.check_encoded_proof_bundle(payload)
    result = subprocess.run(
        [str(LEAN_BUNDLE_VERIFIER), str(artifact)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout.startswith("REJECT\t")
