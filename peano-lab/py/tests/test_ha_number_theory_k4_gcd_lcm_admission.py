"""Public-admission gate for the strict-HA K4 gcd--LCM tranche.

The gate admits only the seven universal-property LCM rows and the complete
reviewed A--I totality bridge.  It binds the public entries byte-for-byte to
their isolated factories, replays the resulting empty-context certificates in
two cold passes, forbids classical ``DNE``, and keeps the other nineteen K4
candidates outside the public registry.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from functools import lru_cache
from hashlib import sha256
from typing import Iterator

from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, Proof
from peano_lab.library.ha_canonical_gcd_candidate import (
    make_ha_canonical_gcd_candidate_theorems,
)
from peano_lab.library.ha_canonical_gcd_edges_candidate import (
    make_ha_canonical_gcd_edges_candidate_theorems,
)
from peano_lab.library.ha_lcm_totality_bridge_candidate import (
    make_ha_lcm_totality_bridge_candidate_theorems,
)
from peano_lab.library.ha_relational_lcm_candidate import (
    make_ha_relational_lcm_candidate_theorems,
)
from peano_lab.library.ha_signed_bezout_gcd_candidate import (
    make_ha_signed_bezout_gcd_candidate_theorems,
)
from peano_lab.library.theorems import (
    HA_LCM_TOTALITY_BRIDGE_THEOREMS,
    HA_NUMBER_THEORY_K4_GCD_LCM_THEOREMS,
    HA_NUMBER_THEORY_TRANCHE01_THEOREMS,
    HA_RELATIONAL_LCM_THEOREMS,
    THEOREMS,
    TheoremSpec,
    _specs_by_name,
    replay,
)


LCM_PUBLIC_NAMES = (
    "is_lcm_multiple_left",
    "is_lcm_multiple_right",
    "is_lcm_least",
    "is_lcm_symm",
    "is_lcm_unique",
    "is_lcm_zero_right",
    "is_lcm_zero_left",
)
BRIDGE_PUBLIC_NAMES = (
    "balanced_bezout_one_implies_coprime",
    "coprime_product_is_lcm",
    "is_lcm_scale_nonzero",
    "balanced_bezout_cancel_gcd",
    "gcd_zero_inputs",
    "gcd_lcm_compatible_exists",
    "lcm_exists_relational",
    "canonical_lcm_exists_unique",
    "gcd_lcm_product",
)
EXPECTED_NAMES = (*LCM_PUBLIC_NAMES, *BRIDGE_PUBLIC_NAMES)

RESIDUAL_PRIVATE_NAMES = (
    "canonical_gcd_exists",
    "canonical_gcd_functional",
    "canonical_gcd_exists_unique",
    "canonical_gcd_zero_right_iff",
    "canonical_gcd_zero_left_iff",
    "canonical_gcd_one_left_iff",
    "canonical_gcd_one_right_iff",
    "canonical_gcd_swap_functional",
    "is_lcm_of_dvd",
    "is_lcm_of_dvd_right",
    "product_common_multiple",
    "is_lcm_refl",
    "is_lcm_one_left",
    "is_lcm_one_right",
    "lcm_zero_left_value",
    "lcm_zero_right_value",
    "lcm_zero_left_exists_unique",
    "lcm_zero_right_exists_unique",
    "gcd_signed_bezout_exists",
)

EXPECTED_STATEMENT_SHA256 = {
    "is_lcm_multiple_left":
        "6bca8a86fc180bd4feba561e4808ce8fd694f687e220137f6be105ef79cf7a43",
    "is_lcm_multiple_right":
        "cfd58405c02982ebe269c680dcb0a62ac0ac33c18c8e9526046c9505f2238c61",
    "is_lcm_least":
        "7d232c7416d15f3cf128a8df8cab34ffc63e906dcc9bd0b33368b4352bd869bf",
    "is_lcm_symm":
        "e5ca139205068d953bb4d9e3c6da0c2501064201ac6ee54bd707640b7c7c30b6",
    "is_lcm_unique":
        "1e8351beb8ca8bd1ab14ce85864e37af888d97f613896316c60ba0dcbc11b48c",
    "is_lcm_zero_right":
        "a84f5e0a22729e73c1a31f5d6e2571fde1ddb828006f96db2070421d1d5e9d87",
    "is_lcm_zero_left":
        "7c6f2f252ee95f63821288659f8208bef80dc883a7927330b337e00711a2f374",
    "balanced_bezout_one_implies_coprime":
        "15ea38440ee20616b269602106c298e93b8e8e2260dda9cf587ebb67cc04601b",
    "coprime_product_is_lcm":
        "ca92cea1f3eaa8750de6280a3e1c2ef0f805d88cd72f1a0a345b44f7f0068c37",
    "is_lcm_scale_nonzero":
        "6ac3b09e048aaea3926dcbe3f2aec301e6c94ae106f32ec142b7d699c01db8ac",
    "balanced_bezout_cancel_gcd":
        "0439333ca1d13314222adf5ab96ec61079fe8d4f738f697ae780db03c750de0e",
    "gcd_zero_inputs":
        "df92b2685a693e5be486c34fddd877b12376cbc23b30b03b6cb3019c111e7350",
    "gcd_lcm_compatible_exists":
        "04331aaa9adc6b04b5aea8dbcac34b46fed098b5233a08b88e957a37b9d7ebd5",
    "lcm_exists_relational":
        "6269a6276e71f62a970b11a696013faf90b5e67ac498f5eb03a2f0f000f0556c",
    "canonical_lcm_exists_unique":
        "708dbaee014b840dcde57d6b0fcd43ca4e484cdaf63db7488391beefe147cf7e",
    "gcd_lcm_product":
        "f3b5095a728faab08137e6ee281f9da8ce6ea2697abd376170c34b1a62d47176",
}

# nodes, depth, objects, edges, reused objects, Cuts, DNE nodes, DAG digest
EXPECTED_RECEIPTS = {
    "is_lcm_multiple_left": (
        21, 13, 21, 20, 0, 0, 0,
        "5c190bf7def19fc23909654cc772afcab5c479fb858898d5f143a80db366e953",
    ),
    "is_lcm_multiple_right": (
        21, 13, 21, 20, 0, 0, 0,
        "f56c306a18651121802b73a86d0beab26f7b595bf569318f7396f3b99c76ca89",
    ),
    "is_lcm_least": (
        24, 16, 24, 23, 0, 0, 0,
        "c1fa2a7ad9ee24262f2d1fe916db3a988dee5da6d53b067be60f378d4456f38b",
    ),
    "is_lcm_symm": (
        36, 21, 36, 35, 0, 0, 0,
        "1651a88cf14cd0940f75b4cad21f75b4d7babd563e6df09ae54442e8fd865b43",
    ),
    "is_lcm_unique": (
        680, 34, 561, 595, 35, 19, 0,
        "28b5d50ea9f274effaecd0ba637805b5535976124380f9647b31cab1b812dc4f",
    ),
    "is_lcm_zero_right": (
        25, 7, 25, 24, 0, 1, 0,
        "1f46d596bf5887fb6fbbf47a571a7773c0e803a57767ddc624a016e3771d1a36",
    ),
    "is_lcm_zero_left": (
        71, 23, 71, 70, 0, 3, 0,
        "a40c084aceae295b1af3ea106a436dfcbb2289b81387ebb03a1bc39c7676fc92",
    ),
    "balanced_bezout_one_implies_coprime": (
        871, 40, 616, 656, 41, 19, 0,
        "6c0e03c2f140d71999c98f4c8a4b15095bc3f922a8a61332a8fb58d9108907a2",
    ),
    "coprime_product_is_lcm": (
        4_191, 53, 1_552, 1_646, 95, 69, 0,
        "c23fbcd7191b32d3d2543edecb330e42719d366fe1c6e99b471299f4314e7b17",
    ),
    "is_lcm_scale_nonzero": (
        430, 27, 371, 383, 13, 10, 0,
        "03918aed31b503afffd000c497bd8442198d370799d046246fdf088bd83ebeee",
    ),
    "balanced_bezout_cancel_gcd": (
        549, 38, 409, 426, 18, 13, 0,
        "a938ef67adb719c111c268255c32f6ad2836ab02da82e2a9113245fd25153bfd",
    ),
    "gcd_zero_inputs": (
        62, 21, 62, 61, 0, 1, 0,
        "b1e47b053b892e56877ab5a4cdd4b6f78ca399957dbf97b97fd427df8676d941",
    ),
    "gcd_lcm_compatible_exists": (
        9_038, 60, 2_390, 2_510, 121, 101, 0,
        "dfe0e69fb172e48b6aa785c0c088ebf1a7cdf09c95ae436305d51d6224e90bc3",
    ),
    "lcm_exists_relational": (
        9_071, 61, 2_423, 2_543, 121, 102, 0,
        "f4e764738627255eb885d78b5cefd74663d68be022370a8036ee450b116a7220",
    ),
    "canonical_lcm_exists_unique": (
        9_791, 62, 2_565, 2_691, 127, 111, 0,
        "3ab4c410a0e4c6717e77d7f951d26304a35b5e9451df299167bb42cadf227747",
    ),
    "gcd_lcm_product": (
        10_441, 61, 2_569, 2_696, 128, 112, 0,
        "c0829496624e993a4c437aa98c32355605109e728acd03d6b5d857fcb5350d0a",
    ),
}


@dataclass(frozen=True, slots=True)
class _Checked:
    formula: Formula
    certificate: Proof


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    lcm = {
        spec.name: spec
        for spec in make_ha_relational_lcm_candidate_theorems(TheoremSpec)
    }
    bridge = {
        spec.name: spec
        for spec in make_ha_lcm_totality_bridge_candidate_theorems(TheoremSpec)
    }
    return tuple(
        (lcm | bridge)[name]
        for name in EXPECTED_NAMES
    )


def _residual_specs() -> tuple[TheoremSpec, ...]:
    lcm = make_ha_relational_lcm_candidate_theorems(TheoremSpec)
    rows = (
        *make_ha_canonical_gcd_candidate_theorems(TheoremSpec),
        *make_ha_canonical_gcd_edges_candidate_theorems(TheoremSpec),
        *(spec for spec in lcm if spec.name not in LCM_PUBLIC_NAMES),
        *make_ha_signed_bezout_gcd_candidate_theorems(TheoremSpec),
    )
    assert tuple(spec.name for spec in rows) == RESIDUAL_PRIVATE_NAMES
    return rows


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


def test_k4_public_registry_has_exact_append_order_and_factory_specs() -> None:
    specs = _candidate_specs()
    assert tuple(spec.name for spec in specs) == EXPECTED_NAMES
    assert tuple(HA_RELATIONAL_LCM_THEOREMS) == specs[:len(LCM_PUBLIC_NAMES)]
    assert tuple(HA_LCM_TOTALITY_BRIDGE_THEOREMS) == specs[len(LCM_PUBLIC_NAMES):]
    assert tuple(HA_NUMBER_THEORY_K4_GCD_LCM_THEOREMS) == specs
    assert {
        spec.name: sha256(spec.statement.encode()).hexdigest()
        for spec in specs
    } == EXPECTED_STATEMENT_SHA256

    public_names = tuple(spec.name for spec in THEOREMS)
    start = public_names.index(EXPECTED_NAMES[0])
    assert public_names[start:start + len(EXPECTED_NAMES)] == EXPECTED_NAMES
    assert start == public_names.index(
        HA_NUMBER_THEORY_TRANCHE01_THEOREMS[-1].name
    ) + 1

    public = _specs_by_name()
    assert all(public[spec.name] == spec for spec in specs)
    assert all(name not in public for name in RESIDUAL_PRIVATE_NAMES)
    assert tuple(spec.name for spec in _residual_specs()) == (
        RESIDUAL_PRIVATE_NAMES
    )


def test_k4_public_admission_preserves_two_cold_intuitionistic_receipts() -> None:
    _, receipts = _admission_runs()
    assert tuple(receipts) == EXPECTED_NAMES
    assert receipts == EXPECTED_RECEIPTS
    assert all(receipt[6] == 0 for receipt in receipts.values())
    assert all(receipt[0] <= 32_768 for receipt in receipts.values())
    assert all(receipt[1] <= 128 for receipt in receipts.values())
    assert all(receipt[2] <= 100_000 for receipt in receipts.values())


def test_k4_public_certificates_reject_false_endpoint_mutations() -> None:
    theorems, _ = _admission_runs()
    specs = {spec.name: spec for spec in _candidate_specs()}
    mutations = {
        "is_lcm_least": lambda statement: statement.replace(
            "exists z. c = l * z",
            "exists z. S c = l * z",
            1,
        ),
        "gcd_lcm_compatible_exists": lambda statement: statement.replace(
            "g * l = a * b",
            "g * l = S (a * b)",
            1,
        ),
        "canonical_lcm_exists_unique": lambda statement: statement.replace(
            "-> m = l)",
            "-> S m = l)",
            1,
        ),
        "gcd_lcm_product": lambda statement: statement.replace(
            "g * l = a * b",
            "g * l = S (a * b)",
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
