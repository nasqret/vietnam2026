"""Public-admission gate for the strict-HA M5 generalized-CRT tranche.

The gate admits exactly the dependency closure of the raw-input constructive
decision endpoint, the conventional solvability equivalence, and the
solution-class/canonical-representative boundary.  It binds all twenty-three
public rows byte-for-byte to their isolated candidate factories, checks their
append order immediately after K4, replays every
empty-context certificate in two cold passes, and rejects classical ``DNE``.
The six residual support/convenience rows remain outside this public tranche.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from functools import lru_cache
from hashlib import sha256
from typing import Iterator

from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, Proof
from peano_lab.library.ha_generalized_crt_canonical_boundary_candidate import (
    make_ha_generalized_crt_canonical_boundary_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_classification_candidate import (
    make_ha_generalized_crt_classification_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_congruence_candidate import (
    make_ha_generalized_crt_congruence_candidate_theorems,
    promoted_mod_eq_add_cancel_left,
)
from peano_lab.library.ha_generalized_crt_decision_candidate import (
    make_ha_generalized_crt_decision_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_sufficiency_candidate import (
    make_ha_generalized_crt_sufficiency_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_total_decision_candidate import (
    make_ha_generalized_crt_total_decision_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_zero_boundary_candidate import (
    make_ha_generalized_crt_zero_boundary_candidate_theorems,
)
from peano_lab.library.theorems import (
    HA_NUMBER_THEORY_K4_GCD_LCM_THEOREMS,
    HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS,
    THEOREMS,
    TheoremSpec,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "mod_eq_zero_iff_eq",
    "mod_eq_scale",
    "crt_solution_pair_congruent",
    "crt_common_solution_implies_gcd_compatible",
    "crt_incompatibility_obstructs_solution",
    "is_gcd_quotients_coprime_nonzero",
    "mod_eq_common_remainder_decomposition",
    "crt_scaled_common_remainder_lift",
    "generalized_binary_crt_sufficient_nonzero",
    "generalized_binary_crt_sufficient_zero_left",
    "generalized_binary_crt_sufficient_zero_right",
    "generalized_binary_crt_sufficient",
    "generalized_binary_crt_solvable_iff",
    "mod_eq_ordered_gap_multiple",
    "mod_eq_lcm_merge",
    "mod_eq_lcm_iff_pair",
    "crt_solution_class_iff_lcm",
    "crt_solution_unique_lcm_zero",
    "crt_solution_canonical_remainder_nonzero",
    "generalized_binary_crt_canonical_boundary",
    "mod_eq_decidable",
    "generalized_binary_crt_solution_or_obstruction",
    "generalized_binary_crt_total_decision",
)

RESIDUAL_PRIVATE_NAMES = (
    "mod_eq_add_cancel_left",
    "mod_eq_add_cancel_right",
    "mod_eq_unscale_nonzero",
    "factor_nonzero_right",
    "is_gcd_nonzero_coprime_quotients",
    "generalized_binary_crt_solvable_iff_nonzero",
)
RESIDUAL_NEW_NAMES = RESIDUAL_PRIVATE_NAMES[1:]

EXPECTED_STATEMENT_SHA256 = {
    "mod_eq_zero_iff_eq":
        "6d14f9a6cc9886ccecbfbe1bef4976e86cae0c38764a0b06f4a8c112de9afc76",
    "mod_eq_scale":
        "c72fce4853757398689509147895a6fe52f096bbb3e48c0270a66dee1377a14a",
    "crt_solution_pair_congruent":
        "a263da6b2728d21e52c9e0721044a430faffb95d1025b266c06305da9a47cba7",
    "crt_common_solution_implies_gcd_compatible":
        "8a8bf920d82502044fdd7e18ed8c275460c55855d3e7989947ac02358d311b43",
    "crt_incompatibility_obstructs_solution":
        "194f4c29faa861337494d12f4e5064fca91cc8a21c4bdfa47560517ccc698a4d",
    "is_gcd_quotients_coprime_nonzero":
        "0bc474f2b82d5fef83c2a189e481247157c496bcb2736b26b1afdf8cac046be3",
    "mod_eq_common_remainder_decomposition":
        "cdb6b4faa868300dad212c67261e39297413f0aaa63cdaaee262ef9c5974776b",
    "crt_scaled_common_remainder_lift":
        "c95894cec0533133e6e90e6e3dec521cebec2addeec0af5641b0840c0f94c8e1",
    "generalized_binary_crt_sufficient_nonzero":
        "beb4079f3e85fbe8451677090e362d1d9c063361c021ca42a45b242789904b33",
    "generalized_binary_crt_sufficient_zero_left":
        "c3bf6a9bee05e47d46ba4f9aa6b2d7ca0d3abdc1a7ef0e413e8acf9fa34a3ee4",
    "generalized_binary_crt_sufficient_zero_right":
        "5bcc9e19a6d128a93af0aff4f682a35a970f6154b66cb1e08a0142ef745c0fb8",
    "generalized_binary_crt_sufficient":
        "11e891144c1e9802af5bc0b3ae6ab3e18d29f329e96da0f1a447240a42d71116",
    "generalized_binary_crt_solvable_iff":
        "a6f60d923d9543160f447e7f43d938f8fbf3eceb49ca17c0b6a3b45bc5b5872c",
    "mod_eq_ordered_gap_multiple":
        "c6d40a1a63937393206bef422e5a44021e14b19cab3b55fdec6ad78238fa64b0",
    "mod_eq_lcm_merge":
        "069eb5e4684895e186da5015966fa347b78403b3848cb8040c812f6bb46abcca",
    "mod_eq_lcm_iff_pair":
        "baa85529864c7d201d6b9320f290e05de84b9f61903ea7970d56abb2ec4fa19d",
    "crt_solution_class_iff_lcm":
        "bf8c300329f1d13f6f62101c6654f17a5369079034e1685c888c25301159e1c9",
    "crt_solution_unique_lcm_zero":
        "d84b07e3b9274fcf8914ad69c75ea56fb64a96268ccc701a5da8aadca9ecc199",
    "crt_solution_canonical_remainder_nonzero":
        "02710fb2f9af9110f8267dd1feef6815040bc92e81337ff3c347282121904056",
    "generalized_binary_crt_canonical_boundary":
        "fc76bb161c4986e700253da58219aa9a37ac39e2f3ebebc64c966c73c696ef75",
    "mod_eq_decidable":
        "b9a37c915c3f13386135830dcc03f17990caf279d6f9f3f7d9cf57539f6b8737",
    "generalized_binary_crt_solution_or_obstruction":
        "54f7722b7e718aff0cd85aeae4ce6b86528892a5e52074d5f2e86eec4d6a3aec",
    "generalized_binary_crt_total_decision":
        "42d29bf501421be60c1a2b14fa858a14abf230eee2f7669503db019d6b014151",
}

# nodes, depth, objects, edges, reused objects, Cuts, DNE nodes, DAG digest
EXPECTED_RECEIPTS = {
    "mod_eq_zero_iff_eq": (
        55, 13, 55, 54, 0, 1, 0,
        "c81d939dd0cdf3b015a50b0d7ca2525670030a44bc07dcc94e53ff3c0d5dc17e",
    ),
    "mod_eq_scale": (
        235, 21, 146, 158, 13, 4, 0,
        "b8a575b14dcef4b063f1973469551f1e1d4bacf5d5e41a85f4c6f45d985735ce",
    ),
    "crt_solution_pair_congruent": (
        307, 31, 259, 274, 16, 8, 0,
        "d4ea11bc6a4450bb6d3fb397defb18f8fcaa53292fcc3bbf6039a4ff9ee1ad1a",
    ),
    "crt_common_solution_implies_gcd_compatible": (
        518, 34, 388, 409, 22, 13, 0,
        "cc5e4988e40ab3710be18c861261101d09b05604a9fb02ce9cbd583aa1c1cecc",
    ),
    "crt_incompatibility_obstructs_solution": (
        560, 35, 430, 451, 22, 14, 0,
        "67f6acd82739752aa50cdbb33e3f02c3542d32de006ef45189f355a236b4b473",
    ),
    "is_gcd_quotients_coprime_nonzero": (
        660, 33, 562, 595, 34, 18, 0,
        "b20e99453775b46993595aa0c53a4e8facc56e037ef7d138d3005098d1bf973d",
    ),
    "mod_eq_common_remainder_decomposition": (
        2_894, 69, 1_075, 1_138, 64, 43, 0,
        "7615686f1fb9c23b0b53a4cc46a1da5349bd6fd6b808d8ef0203b45a213fd6fc",
    ),
    "crt_scaled_common_remainder_lift": (
        5_745, 52, 2_062, 2_174, 113, 92, 0,
        "188a46f051c74f8a3f53c3945a3760fff3be12df5d89c2b468e94cf201166674",
    ),
    "generalized_binary_crt_sufficient_nonzero": (
        9_482, 74, 3_147, 3_302, 156, 141, 0,
        "9c1ad09a4bfb2ee8e273320069d6ef6f9e50c0229aa023bb45cf887ddd9c2a1b",
    ),
    "generalized_binary_crt_sufficient_zero_left": (
        834, 37, 682, 717, 36, 26, 0,
        "074f07df173308477693b6e3bbfd3a3a4123078d8f7f5eaac9077666d3cbc763",
    ),
    "generalized_binary_crt_sufficient_zero_right": (
        805, 36, 653, 688, 36, 26, 0,
        "da2d830f65077816dfeecd1503a787cf8ba0f5ec99e93d13b5456e4ba772e2f6",
    ),
    "generalized_binary_crt_sufficient": (
        11_240, 78, 3_495, 3_662, 168, 160, 0,
        "931fbcc775154507996c768cb1de1cc8479c3ed805ce0d1a95fffb530e8b56c4",
    ),
    "generalized_binary_crt_solvable_iff": (
        11_825, 80, 3_658, 3_830, 173, 168, 0,
        "3f1d82f0f06df9e0d2a5c746405ee46406db71c57e4bbf32f68792be07af8b0c",
    ),
    "mod_eq_ordered_gap_multiple": (
        558, 30, 310, 325, 16, 13, 0,
        "6a30012cfc1213bf167be2de794e05cdae2893ab075cfc24abf9b181bde9be67",
    ),
    "mod_eq_lcm_merge": (
        1_315, 33, 653, 685, 33, 25, 0,
        "46cd67f69ccf0c669de283fca6a74a0a85cf18d54f248f1a6f428122196a331b",
    ),
    "mod_eq_lcm_iff_pair": (
        1_570, 37, 864, 908, 45, 32, 0,
        "855d5745c1613304fc0a5f26c70fe9f795ed3ebcff4a7276e3745681d41fc91a",
    ),
    "crt_solution_class_iff_lcm": (
        2_208, 39, 1_055, 1_104, 50, 40, 0,
        "305a913aaca1c3e307d8ca77bb90c063dd67f3fa9f9bdd69e28cf4064cdff7b3",
    ),
    "crt_solution_unique_lcm_zero": (
        2_300, 40, 1_126, 1_176, 51, 43, 0,
        "2afc46ac88613c95400eb37f80b1fbda095b18a7f6a774255426b48c35aed9ac",
    ),
    "crt_solution_canonical_remainder_nonzero": (
        4_086, 65, 1_668, 1_746, 79, 64, 0,
        "091e8f2b1ba7e4665b87071fcd924ea1098880d65a97bcdd264ed544e33ff0e4",
    ),
    "generalized_binary_crt_canonical_boundary": (
        17_750, 80, 4_239, 4_426, 188, 193, 0,
        "c704a17f6feed83142b160bbeafcc14764d5ae6590999187eed5455c3ad03bd7",
    ),
    "mod_eq_decidable": (
        2_339, 70, 1_217, 1_278, 62, 44, 0,
        "298e2b18fff84bcf3a2ec69dbc464454f958d4155b7afb687f0bab2fd95efe7e",
    ),
    "generalized_binary_crt_solution_or_obstruction": (
        14_182, 80, 3_909, 4_090, 182, 182, 0,
        "16e7cb1c430fa4e17ea878adc72d34c92e0bc3f135c4a3cf24cb2a296b38e525",
    ),
    "generalized_binary_crt_total_decision": (
        15_492, 82, 4_052, 4_240, 189, 192, 0,
        "c2d915d2eb60ccbb2dac9f31e9e1f9c310c28264b74483ec97ae33a1a0d965ee",
    ),
}


@dataclass(frozen=True, slots=True)
class _Checked:
    formula: Formula
    certificate: Proof


def _all_new_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_ha_generalized_crt_congruence_candidate_theorems(TheoremSpec),
        *make_ha_generalized_crt_sufficiency_candidate_theorems(TheoremSpec),
        *make_ha_generalized_crt_zero_boundary_candidate_theorems(TheoremSpec),
        *make_ha_generalized_crt_classification_candidate_theorems(TheoremSpec),
        *make_ha_generalized_crt_canonical_boundary_candidate_theorems(TheoremSpec),
        *make_ha_generalized_crt_decision_candidate_theorems(TheoremSpec),
        *make_ha_generalized_crt_total_decision_candidate_theorems(TheoremSpec),
    )


def _partitioned_specs() -> tuple[tuple[TheoremSpec, ...], tuple[TheoremSpec, ...]]:
    rows = _all_new_specs()
    by_name = {spec.name: spec for spec in rows}
    assert len(rows) == len(by_name) == 28
    assert set(by_name) == set(EXPECTED_NAMES) | set(RESIDUAL_NEW_NAMES)
    return (
        tuple(by_name[name] for name in EXPECTED_NAMES),
        tuple(by_name[name] for name in RESIDUAL_NEW_NAMES),
    )


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return _partitioned_specs()[0]


def _residual_specs() -> tuple[TheoremSpec, ...]:
    return _partitioned_specs()[1]


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


def _cold_pass() -> tuple[dict[str, _Checked], dict[str, tuple[object, ...]]]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    public = _specs_by_name()
    specs = _candidate_specs()
    assert all(public[spec.name] == spec for spec in specs)

    theorems: dict[str, _Checked] = {}
    receipts: dict[str, tuple[object, ...]] = {}
    for spec in specs:
        checked = replay(spec.name)
        assert checked.formula == parse_formula(spec.statement)
        assert check((), checked.certificate, checked.formula)
        unique_nodes = tuple(_walk_unique(checked.certificate))
        nodes, depth = proof_metrics(checked.certificate)
        objects, edges, reused = proof_identity_metrics(checked.certificate)
        assert objects == len(unique_nodes)
        receipts[spec.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique_nodes),
            sum(type(node) is DNE for node in unique_nodes),
            _proof_dag_digest(checked.certificate),
        )
        theorems[spec.name] = _Checked(
            checked.formula,
            checked.certificate,
        )
    return theorems, receipts


@lru_cache(maxsize=1)
def _admission_runs():
    first_theorems, first_receipts = _cold_pass()
    _, second_receipts = _cold_pass()
    assert second_receipts == first_receipts
    return first_theorems, first_receipts


def test_m5_public_registry_has_exact_append_order_and_factory_specs() -> None:
    specs = _candidate_specs()
    residual = _residual_specs()
    support = promoted_mod_eq_add_cancel_left(TheoremSpec)
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert tuple(spec.name for spec in residual) == RESIDUAL_NEW_NAMES
    assert support.name == RESIDUAL_PRIVATE_NAMES[0]
    assert tuple(HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS) == specs
    assert {
        spec.name: sha256(spec.statement.encode()).hexdigest()
        for spec in specs
    } == EXPECTED_STATEMENT_SHA256

    public_names = tuple(spec.name for spec in THEOREMS)
    start = public_names.index(EXPECTED_NAMES[0])
    assert public_names[start:start + len(EXPECTED_NAMES)] == EXPECTED_NAMES
    assert start == public_names.index(
        HA_NUMBER_THEORY_K4_GCD_LCM_THEOREMS[-1].name
    ) + 1

    public = _specs_by_name()
    assert all(public[spec.name] == spec for spec in specs)
    assert all(name not in public for name in RESIDUAL_PRIVATE_NAMES)
    assert all(
        spec not in HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS
        for spec in residual
    )
    assert support not in HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS


def test_m5_public_admission_preserves_two_cold_intuitionistic_receipts() -> None:
    _, receipts = _admission_runs()
    assert tuple(receipts) == EXPECTED_NAMES
    assert receipts == EXPECTED_RECEIPTS
    assert all(receipt[6] == 0 for receipt in receipts.values())
    assert all(receipt[0] <= MAX_LIVE_PROOF_NODES for receipt in receipts.values())
    assert all(receipt[1] <= MAX_LIVE_PROOF_DEPTH for receipt in receipts.values())
    assert all(receipt[2] <= MAX_LIVE_PROOF_OBJECTS for receipt in receipts.values())


def test_m5_public_certificates_reject_false_endpoint_mutations() -> None:
    theorems, _ = _admission_runs()
    specs = {spec.name: spec for spec in _candidate_specs()}
    mutations = {
        "mod_eq_zero_iff_eq": lambda statement: statement.replace(
            "-> a = b) /\\", "-> S a = b) /\\", 1
        ),
        "generalized_binary_crt_solvable_iff": lambda statement:
            statement.replace("a + m *", "S a + m *", 1),
        "generalized_binary_crt_canonical_boundary": lambda statement:
            statement.replace("-> y = x", "-> S y = x", 1),
        "generalized_binary_crt_solution_or_obstruction": lambda statement:
            statement.replace(
                "a + g * hgcrt_mod_left_decision_boundary_incompatible",
                "S a + g * hgcrt_mod_left_decision_boundary_incompatible",
                1,
            ),
        "generalized_binary_crt_total_decision": lambda statement:
            statement.replace(
                "m = g * hag_left_factor_total_decision",
                "S m = g * hag_left_factor_total_decision",
                1,
            ),
    }
    for name, mutate in mutations.items():
        statement = specs[name].statement
        false_statement = mutate(statement)
        assert false_statement != statement
        assert not check(
            (),
            theorems[name].certificate,
            parse_formula(false_statement),
        )
