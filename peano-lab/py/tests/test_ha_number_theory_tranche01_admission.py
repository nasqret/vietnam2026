"""Post-admission receipt for HA number-theory tranche 01.

This focused audit closes exactly nine isolated candidates: the canonical
remainder package, its canonical-congruence bridge, the canonical bounded
modular-inverse package, and only the Wilson point lemma needed for inverse
uniqueness.  Candidate bodies are replayed with their declared dependencies,
those dependency introductions are peeled, and every dependency is discharged
recursively by an ordinary kernel ``Cut``.  Public dependencies come only from
the public replay path.

Passing this file proves that each deliberately enrolled public specification
is byte-for-byte equal to its isolated factory specification and retains the
same deterministic empty-context certificate receipt.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterator

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, Imp, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.ha_canonical_congruence_candidate import (
    make_ha_canonical_congruence_candidate_theorems,
)
from peano_lab.library.ha_canonical_remainder_candidate import (
    make_ha_canonical_remainder_candidate_theorems,
)
from peano_lab.library.ha_modular_inverse_candidate import (
    make_ha_modular_inverse_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)
from peano_lab.library.wilson_inverse_point_candidate import (
    make_wilson_inverse_point_candidate_theorems,
)


EXPECTED_NAMES = (
    "canonical_remainder_exists",
    "canonical_remainder_functional",
    "canonical_remainder_zero_impossible",
    "canonical_remainder_exists_unique",
    "canonical_remainders_characterize_mod_eq",
    "bounded_mod_inverse_unique",
    "coprime_bounded_mod_inverse",
    "mod_inverse_implies_coprime",
    "coprime_iff_unique_bounded_mod_inverse",
)

# Structural occurrences/depth followed by distinct proof objects, object
# edges, and reused object references.  Cut counts and certificate digests are
# pinned below after the same content-stable DAG traversal used by the QR gate.
EXPECTED_METRICS = {
    "canonical_remainder_exists": (238, 29, 215, 230, 16),
    "canonical_remainder_functional": (885, 58, 575, 596, 22),
    "canonical_remainder_zero_impossible": (21, 13, 21, 20, 0),
    "canonical_remainder_exists_unique": (1_148, 60, 765, 803, 39),
    "canonical_remainders_characterize_mod_eq": (1_888, 64, 908, 950, 43),
    "bounded_mod_inverse_unique": (2_914, 68, 1_001, 1_061, 61),
    "coprime_bounded_mod_inverse": (5_675, 53, 1_752, 1_853, 102),
    "mod_inverse_implies_coprime": (874, 40, 602, 643, 42),
    "coprime_iff_unique_bounded_mod_inverse": (9_512, 70, 2_538, 2_679, 142),
}
EXPECTED_CUTS = {
    "canonical_remainder_exists": 6,
    "canonical_remainder_functional": 17,
    "canonical_remainder_zero_impossible": 1,
    "canonical_remainder_exists_unique": 25,
    "canonical_remainders_characterize_mod_eq": 32,
    "bounded_mod_inverse_unique": 42,
    "coprime_bounded_mod_inverse": 88,
    "mod_inverse_implies_coprime": 20,
    "coprime_iff_unique_bounded_mod_inverse": 126,
}
EXPECTED_CERTIFICATE_SHA256 = {
    "canonical_remainder_exists":
        "e94dc6590d4a48e5d9836d9a343642bb9d0d03df4120697ae33469d1dedd1e90",
    "canonical_remainder_functional":
        "9fc9204b6c8fb5485026b3d2b70bc37e981eb63024078e23493d6de25712e039",
    "canonical_remainder_zero_impossible":
        "9a9d6722c6f90b895c5dd93408ffee50bcd12d8de5bc7eefe8321e4db6c8241b",
    "canonical_remainder_exists_unique":
        "b3bc67d9eb55c2f9dcca218bc2a2c5f3933af683553fa68769b376437bb0458d",
    "canonical_remainders_characterize_mod_eq":
        "451657b14f19132e48bfb6ae85bfe9861c145db890f841d35f52bc08b199e78b",
    "bounded_mod_inverse_unique":
        "6fe8ceff81c32868d871179c063f93264bd4fb6fb545f0b58f2855cb5b30e865",
    "coprime_bounded_mod_inverse":
        "779ff00cd6d4b8a193dd358f924084a3f3c955a52f96a6a01b5a97e22d2d4e33",
    "mod_inverse_implies_coprime":
        "d238282c7443e9f74ed1eb75ddf13ca548e19a5b5859f49f52ad28231a512e9e",
    "coprime_iff_unique_bounded_mod_inverse":
        "c3ed07e7caef52895001332d066ae9e4ce25167c7a0cd7189f8957c9aa7dc9f3",
}

CAMPAIGN_PATH = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "arithmetic-library"
    / "ha-number-theory-campaign.json"
)


@dataclass(frozen=True, slots=True)
class _Checked:
    formula: Formula
    certificate: Proof


@dataclass(frozen=True, slots=True)
class _Receipt:
    name: str
    nodes: int
    depth: int
    objects: int
    edges: int
    reused: int
    cuts: int
    certificate_sha256: str


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    remainders = make_ha_canonical_remainder_candidate_theorems(TheoremSpec)
    congruences = make_ha_canonical_congruence_candidate_theorems(TheoremSpec)
    inverses = make_ha_modular_inverse_candidate_theorems(TheoremSpec)
    wilson = tuple(
        spec
        for spec in make_wilson_inverse_point_candidate_theorems(TheoremSpec)
        if spec.name == "bounded_mod_inverse_unique"
    )

    assert len(remainders) == 4
    assert len(congruences) == 1
    assert len(inverses) == 3
    assert len(wilson) == 1

    by_name = {
        spec.name: spec
        for spec in (*remainders, *congruences, *inverses, *wilson)
    }
    assert len(by_name) == len(EXPECTED_NAMES)
    return tuple(by_name[name] for name in EXPECTED_NAMES)


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique(proof: Proof) -> Iterator[Proof]:
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


def _proof_dag_digest(proof: Proof) -> str:
    """Hash proof content bottom-up while charging shared objects once."""

    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend(
                (child, False)
                for child in children
                if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _fresh_replayer():
    specs = _candidate_specs()
    local = {spec.name: spec for spec in specs}
    public = _specs_by_name()

    assert tuple(local) == EXPECTED_NAMES
    assert all(public[name] == local[name] for name in local)

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        if name in public:
            checked = replay(name)
            return _Checked(checked.formula, checked.certificate)

        spec = local[name]
        formula = _closed_formula(spec.statement)
        dependency_specs = tuple(
            local.get(dependency) or public[dependency]
            for dependency in spec.dependencies
        )
        target = formula
        for dependency_spec in reversed(dependency_specs):
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        certificate = checked_final(state, target)

        body = certificate
        for dependency in spec.dependencies:
            assert type(body) is ImpIntro, (
                f"{spec.name} did not expose dependency {dependency}"
            )
            body = body.body
        for dependency in reversed(spec.dependencies):
            checked_dependency = run(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )

        assert check((), body, formula)
        return _Checked(formula, body)

    return specs, run


def _cold_pass() -> tuple[dict[str, _Checked], tuple[_Receipt, ...]]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, run = _fresh_replayer()
    theorems: dict[str, _Checked] = {}
    receipts: list[_Receipt] = []
    for spec in specs:
        theorem = run(spec.name)
        theorems[spec.name] = theorem
        assert theorem.formula == parse_formula(spec.statement)
        assert check((), theorem.certificate, theorem.formula)

        unique_nodes = tuple(_walk_unique(theorem.certificate))
        assert not any(type(node) is DNE for node in unique_nodes)
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        assert objects == len(unique_nodes)
        receipts.append(
            _Receipt(
                name=spec.name,
                nodes=nodes,
                depth=depth,
                objects=objects,
                edges=edges,
                reused=reused,
                cuts=sum(type(node) is Cut for node in unique_nodes),
                certificate_sha256=_proof_dag_digest(theorem.certificate),
            )
        )
    return theorems, tuple(receipts)


@lru_cache(maxsize=1)
def _admission_runs():
    first_theorems, first_receipts = _cold_pass()
    _, second_receipts = _cold_pass()
    assert second_receipts == first_receipts
    return first_theorems, first_receipts


def test_tranche01_public_admission_preserves_exact_closure_receipts() -> None:
    theorems, receipts = _admission_runs()

    assert tuple(receipt.name for receipt in receipts) == EXPECTED_NAMES
    assert {
        receipt.name: (
            receipt.nodes,
            receipt.depth,
            receipt.objects,
            receipt.edges,
            receipt.reused,
        )
        for receipt in receipts
    } == EXPECTED_METRICS
    assert {receipt.name: receipt.cuts for receipt in receipts} == EXPECTED_CUTS
    assert {
        receipt.name: receipt.certificate_sha256 for receipt in receipts
    } == EXPECTED_CERTIFICATE_SHA256
    assert set(theorems) == set(EXPECTED_NAMES)

    # Admission is explicit data in the public registry; equality with each
    # isolated factory prevents the migration from changing a statement,
    # dependency, script, or summary.
    public = _specs_by_name()
    local = {spec.name: spec for spec in _candidate_specs()}
    assert all(public[name] == local[name] for name in EXPECTED_NAMES)


def test_campaign_manifest_is_bound_to_the_exact_admission_receipts() -> None:
    theorems, receipts = _admission_runs()
    manifest = json.loads(CAMPAIGN_PATH.read_text(encoding="utf-8"))
    evidence = manifest["theorem_evidence"]

    assert evidence["receipt_kind"] == "empty_context_intuitionistic_cut_closure"
    assert evidence["determinism_passes"] == 2
    assert evidence["dne_nodes"] == 0
    assert evidence["test_paths"] == [
        "peano-lab/py/tests/test_ha_number_theory_tranche01_admission.py",
        "peano-lab/py/tests/test_ha_canonical_gcd_candidate.py",
        "peano-lab/py/tests/test_ha_canonical_gcd_edges_candidate.py",
        "peano-lab/py/tests/test_ha_signed_parity_candidate.py",
        "peano-lab/py/tests/test_ha_signed_decode_candidate.py",
        "peano-lab/py/tests/test_ha_signed_code_extensional_candidate.py",
        "peano-lab/py/tests/test_ha_signed_balance_candidate.py",
        "peano-lab/py/tests/test_ha_signed_balance_complete_candidate.py",
        "peano-lab/py/tests/test_ha_signed_negate_candidate.py",
        "peano-lab/py/tests/test_ha_signed_add_candidate.py",
        "peano-lab/py/tests/test_ha_signed_add_laws_candidate.py",
        "peano-lab/py/tests/test_ha_signed_add_associative_candidate.py",
        "peano-lab/py/tests/test_ha_signed_mul_candidate.py",
        "peano-lab/py/tests/test_ha_signed_mul_laws_candidate.py",
        "peano-lab/py/tests/test_ha_signed_mul_associative_candidate.py",
        "peano-lab/py/tests/test_ha_signed_mul_distributive_candidate.py",
            "peano-lab/py/tests/test_ha_signed_nat_scale_candidate.py",
            "peano-lab/py/tests/test_ha_signed_nat_scale_laws_candidate.py",
            "peano-lab/py/tests/test_ha_signed_bezout_candidate.py",
            "peano-lab/py/tests/test_ha_pair_cell_seed_candidate.py",
            "peano-lab/py/tests/test_ha_pair_shell_candidate.py",
            "peano-lab/py/tests/test_ha_pair_injective_candidate.py",
            "peano-lab/py/tests/test_ha_signed_bezout_gcd_candidate.py",
        "peano-lab/py/tests/test_ha_relational_lcm_candidate.py",
        "peano-lab/py/tests/test_ha_lcm_totality_bridge_candidate.py",
        "peano-lab/py/tests/test_ha_number_theory_k4_gcd_lcm_admission.py",
        "peano-lab/py/tests/test_ha_generalized_crt_congruence_candidate.py",
        "peano-lab/py/tests/test_ha_generalized_crt_sufficiency_candidate.py",
        "peano-lab/py/tests/test_ha_generalized_crt_zero_boundary_candidate.py",
        "peano-lab/py/tests/test_ha_generalized_crt_classification_candidate.py",
        "peano-lab/py/tests/test_ha_generalized_crt_canonical_boundary_candidate.py",
        "peano-lab/py/tests/test_ha_generalized_crt_decision_candidate.py",
        "peano-lab/py/tests/test_ha_generalized_crt_total_decision_candidate.py",
        "peano-lab/py/tests/test_ha_number_theory_m5_generalized_crt_admission.py",
    ]

    items = evidence["theorems"][: len(EXPECTED_NAMES)]
    assert tuple(item["name"] for item in items) == EXPECTED_NAMES
    specs = {spec.name: spec for spec in _candidate_specs()}
    receipt_by_name = {receipt.name: receipt for receipt in receipts}
    for item in items:
        name = item["name"]
        assert item["status"] == "public_checked"
        assert item["statement_sha256"] == sha256(
            specs[name].statement.encode()
        ).hexdigest()
        receipt = receipt_by_name[name]
        assert item["receipt"] == {
            "nodes": receipt.nodes,
            "depth": receipt.depth,
            "objects": receipt.objects,
            "edges": receipt.edges,
            "reused": receipt.reused,
            "cuts": receipt.cuts,
            "certificate_sha256": receipt.certificate_sha256,
        }
        assert check((), theorems[name].certificate, theorems[name].formula)


def test_campaign_roots_reject_nearby_false_closed_targets() -> None:
    theorems, _ = _admission_runs()
    specs = {spec.name: spec for spec in _candidate_specs()}
    mutations = {
        "canonical_remainder_exists_unique": lambda statement: statement.replace(
            "-> s = r)",
            "-> S s = r)",
            1,
        ),
        "canonical_remainders_characterize_mod_eq": lambda statement: statement.replace(
            "-> r = s) /\\ (r = s ->",
            "-> S r = s) /\\ (r = s ->",
            1,
        ),
        "coprime_iff_unique_bounded_mod_inverse": lambda statement: statement.replace(
            "hmi_comparison_package_result = hmi_solution_package_result",
            "S hmi_comparison_package_result = hmi_solution_package_result",
            1,
        ),
    }

    for name, mutate in mutations.items():
        statement = specs[name].statement
        false_statement = mutate(statement)
        assert false_statement != statement
        false_target = parse_formula(false_statement)
        assert not check((), theorems[name].certificate, false_target)
