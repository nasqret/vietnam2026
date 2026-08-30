"""Exact browser-safe v31 proof providers for the completed lower campaigns.

The nineteen artifacts are unchanged research proof data. Enrollment metadata
is not proof authority: every actual dependency body must pass the original HA
kernel on checked use. This module imports no authoring registry and never
loads a repository catalogue. Independent Lean checking belongs to release
verification, not to this runtime or its metadata seal.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from ..kernel.formulas import Formula
from .campaign_lower_layer_closure import _packaging_root, _specs_digest
from .proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, BundleNode, CheckedProofBundle, ProofBundle,
    check_proof_bundle,
)
from .theorems import TheoremSpec, _closed_formula


class CompletedLowerClosureError(ValueError):
    """A frozen source, exact dependency, target, proof, or resource gate failed."""


@dataclass(frozen=True, slots=True)
class CompletedLowerFactory:
    campaign: str
    module: str
    factory: str
    rfc: str
    source_bytes: int
    source_sha256: str
    count: int
    specs_sha256: str

    @property
    def source(self) -> str:
        return f"peano-lab/py/peano_lab/library/{self.module}.py"

    @property
    def test(self) -> str:
        return f"peano-lab/py/tests/test_{self.module}.py"


@dataclass(frozen=True, slots=True)
class CompletedLowerFamily:
    slug: str
    generation: int
    artifact: str
    artifact_bytes: int
    artifact_sha256: str
    count: int
    specs_sha256: str
    names_sha256: str
    edge_count: int
    command_count: int
    rfc: str
    owned_names: tuple[str, ...]
    principal_roots: tuple[str, ...]
    theorem_count: int
    root_names: tuple[str, ...]
    node_count: int
    dependency_edges: int
    bundle_edges: int
    body_nodes: int
    ordered_cone_names_sha256: str
    complete_non_alpha_specs_sha256: str
    modules: tuple[str, ...]
    principal_pins: tuple[tuple[str, str], ...]

    @property
    def artifact_filename(self) -> str:
        return self.artifact.rsplit("/", 1)[-1]

    @property
    def principal_statement_sha256(self) -> Mapping[str, str]:
        return MappingProxyType(dict(self.principal_pins))


@dataclass(frozen=True, slots=True)
class CompletedLowerRow:
    node_id: int
    inventory_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    campaign: str | None
    is_owned: bool


@dataclass(frozen=True, slots=True)
class CompletedLowerPlan:
    family: CompletedLowerFamily
    rows: tuple[CompletedLowerRow, ...]
    specs: tuple[TheoremSpec, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    owned_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    frontier_specs_sha256: str

    @property
    def positions(self) -> Mapping[str, int]:
        return MappingProxyType({row.name: row.node_id for row in self.rows})


PARENT_ALPHA_V30_COUNT = 3222
PARENT_ALPHA_V30_SPECS_SHA256 = "0c0920378ae30b41375716f31822b008ad2ced47c3ae72707dbf6e55336f59e1"
PARENT_ALPHA_V30_IDENTITY_SHA256 = "8986ab8b8d8493ab7c8f01e2080b0ac590fd3c7289ac811b6606710ca453e1e9"
PARENT_ALPHA_V30_ENROLLMENT_SHA256 = "04b73a38d04d1bd8038c1712b7f4f6cc77156f97a890515524761bb1cdf71393"
EXPECTED_COMPLETED_LOWER_COUNT = 574
EXPECTED_COMPLETED_LOWER_EDGE_COUNT = 1660
EXPECTED_COMPLETED_LOWER_COMMAND_COUNT = 26004
EXPECTED_COMPLETED_LOWER_NAMES_SHA256 = "594e3c4766d7bcfcfafbbf6882e12f736914c9291788f548e34af12c1c6293d7"
EXPECTED_COMPLETED_LOWER_SPECS_SHA256 = "9ce681cbca759fcc555f582158162e9ba9cb6dbed64b57274fca530435c8c994"
EXPECTED_COMPLETED_LOWER_FAMILY_COUNT = 19
EXPECTED_COMPLETED_LOWER_FACTORY_COUNT = 35
EXPECTED_COMPLETED_LOWER_METADATA_SHA256 = "07c04a017f2a19e2250b6b9a013b247cc94586ce90ab818bc75a7e20e1ea7737"
# The existing source-input and proof-bundle ceilings, not enlarged limits.
MAX_SOURCE_BYTES = 2 * 1024 * 1024

FACTORIES = (
    CompletedLowerFactory(
        "euler-units",
        "euler_units_residue_candidate",
        "make_euler_units_residue_candidate_theorems",
        "euler-units-rfc-v1.md",
        16354,
        "dacb55219a5a5e9856d208a73e39b77156977d1de7d882044d4ed52907a7fdee",
        12,
        "bf5ffbf1b7cf4f5a23b36a3c67873ce8f02d533b3dabd458cec7c8ebe1498fcb",
    ),
    CompletedLowerFactory(
        "euler-units",
        "euler_units_product_candidate",
        "make_euler_units_product_candidate_theorems",
        "euler-units-rfc-v1.md",
        16561,
        "dfbbc7dd69672992eb99a4eb99f64fb8273c28838aa6e1e749eb5b8a075ef8b9",
        14,
        "06d4d13cb8db6555b1fad3a696882256c8374d61dede4d3321e590fb2c0e29ee",
    ),
    CompletedLowerFactory(
        "euler-units",
        "euler_units_candidate",
        "make_euler_units_candidate_theorems",
        "euler-units-rfc-v1.md",
        12657,
        "46e69f301a7215929958726a12ee151ad1972b771bcee57250a8fbbf18873458",
        6,
        "23b1fb1707e6dca129bcef95a7a76363703caced67aa6bc35d76acea0a504e70",
    ),
    CompletedLowerFactory(
        "prime-fields",
        "prime_field_arithmetic_candidate",
        "make_prime_field_arithmetic_candidate_theorems",
        "prime-field-arithmetic-rfc-v1.md",
        39963,
        "d4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90",
        42,
        "c094cd2353487319cb7b68f207ad63db68b113b90a7b4cfbbf70e3d4b3b754d8",
    ),
    CompletedLowerFactory(
        "prime-fields",
        "prime_field_tables_candidate",
        "make_prime_field_tables_candidate_theorems",
        "prime-field-arithmetic-rfc-v1.md",
        28103,
        "2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400",
        31,
        "ba753fb0d37ed8c3a35739ba5029da4fcd3f147c654554836febfcf8092c8eba",
    ),
    CompletedLowerFactory(
        "prime-fields",
        "prime_field_finiteness_candidate",
        "make_prime_field_finiteness_candidate_theorems",
        "prime-field-arithmetic-rfc-v1.md",
        22709,
        "a86bc0d8913ebfc1ea84c8dad691db5f90e21029c612ee87ad804657b1971b28",
        14,
        "6696c54cd28bb6cbc82e3ad0525cc9bd1a237b318ab295f81ceb9d3b7d0ed1e7",
    ),
    CompletedLowerFactory(
        "mobius-values",
        "mobius_value_candidate",
        "make_mobius_value_candidate_theorems",
        "mobius-divisor-sum-foundations-rfc-v1.md",
        14175,
        "18cc5aef4d4710a09bd8f2eac063ae2ccf54049a68eaab33d6b9ce7df87af9e0",
        13,
        "a0320f2e312d3e3c953a178585be97db32abae5e3a36b243a214819460b9764e",
    ),
    CompletedLowerFactory(
        "mobius-values",
        "mobius_prime_step_candidate",
        "make_mobius_prime_step_candidate_theorems",
        "mobius-divisor-sum-foundations-rfc-v1.md",
        12550,
        "f6fe75aa8e5c899baff761edea21dc82a3b76ea52ef165511d20f34a6d332af7",
        8,
        "db443efe6059cc8928e842e0d44cf7b7440c89cca2928b87950a9820dfc98909",
    ),
    CompletedLowerFactory(
        "signed-sums",
        "divisor_sum_table_candidate",
        "make_divisor_sum_table_candidate_theorems",
        "mobius-divisor-sum-foundations-rfc-v1.md",
        20337,
        "011980a3d5857c123e97359e048bb7f5b9e35685fb9d1357d1d543c4ff9d7692",
        14,
        "fcff0f2352734c03918deb20e6a03dbebf3d16eb9b64816ecaaf21249a4daae0",
    ),
    CompletedLowerFactory(
        "signed-sums",
        "divisor_sum_algebra_candidate",
        "make_divisor_sum_algebra_candidate_theorems",
        "mobius-divisor-sum-foundations-rfc-v1.md",
        15382,
        "38cdcf7229cb43001f658bded3434d53b54efee3b28067f634e1f39af61a6c92",
        9,
        "635b5a3603e00d2d5de99ab488f8e7ccde254bbb918edbd0727984ff5d21f93a",
    ),
    CompletedLowerFactory(
        "signed-sums",
        "divisor_sum_reindex_candidate",
        "make_divisor_sum_reindex_candidate_theorems",
        "mobius-divisor-sum-foundations-rfc-v1.md",
        12952,
        "e652ac90350d01c0ec6e4bbb7405950db316f35ff24fba3d019e1bc0c21d1ab4",
        7,
        "5b0a4ffeeed9b7e453bf70e8267e154a95ba4339ee14554061004b6276e19e10",
    ),
    CompletedLowerFactory(
        "divisor-sums",
        "arithmetic_table_extension_candidate",
        "make_arithmetic_table_extension_candidate_theorems",
        "mobius-tables-divisor-sums-rfc-v1.md",
        10204,
        "d39d08f7178b526daad51aaf4a75c325f567424bb8ae74906c030f4d72e9e294",
        7,
        "fa5d45bebb5388d84e69882b0d37e007433f45bcfc916def8e8b5c5cc06394bf",
    ),
    CompletedLowerFactory(
        "divisor-sums",
        "mobius_table_candidate",
        "make_mobius_table_candidate_theorems",
        "mobius-tables-divisor-sums-rfc-v1.md",
        11544,
        "7631337dd93f4a65e6f74ce9a5129d6701a496aa49969764c0945f4248676fc4",
        8,
        "0a2ee2975d69f7928ad9e7f992f87cb8497e005acf8a26abe60f50a6efd843c7",
    ),
    CompletedLowerFactory(
        "divisor-sums",
        "divisor_mask_candidate",
        "make_divisor_mask_candidate_theorems",
        "mobius-tables-divisor-sums-rfc-v1.md",
        26068,
        "740efabb5cbf6e0c804e901dae423e319c52c86f605ebe2a4ad0bffb033d9543",
        22,
        "b0a4e63dfd434f8d380144cb9b45565e692752a58a8ef254b946a8ae9796a4bc",
    ),
    CompletedLowerFactory(
        "signed-weighted-sums",
        "signed_table_operations_candidate",
        "make_signed_table_operations_candidate_theorems",
        "signed-weighted-sums-rfc-v1.md",
        19549,
        "465e623dbe3fcac0eb70ca72e890d1cc8046b3a476014dc65d187b3f30f4893f",
        23,
        "0258c13b44a1c847525f65e6c4cd76e995ba220f941f71a5b62c5a73bd5a7f93",
    ),
    CompletedLowerFactory(
        "signed-weighted-sums",
        "signed_sum_linearity_candidate",
        "make_signed_sum_linearity_candidate_theorems",
        "signed-weighted-sums-rfc-v1.md",
        11817,
        "8da9d92ec3e204583e7539fc2ff6ca7af5677a909a59831951e978deab9d69c0",
        7,
        "39e7609dded1ac5fe6263d2834ade28606355ae5188c9098810cf54641d4f268",
    ),
    CompletedLowerFactory(
        "signed-weighted-sums",
        "signed_weighted_sum_candidate",
        "make_signed_weighted_sum_candidate_theorems",
        "signed-weighted-sums-rfc-v1.md",
        13320,
        "2cbbb6486f0a75bbf97165018ef7539dd90c8a06317d0ed037ed95afcc72db07",
        10,
        "366f9639b631497d9d4938e35f2eb49aaa7205079ad515c32db1f729b74f702a",
    ),
    CompletedLowerFactory(
        "prime-field-polynomials",
        "prime_field_polynomial_candidate",
        "make_prime_field_polynomial_candidate_theorems",
        "prime-field-polynomials-rfc-v1.md",
        45723,
        "644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72",
        31,
        "1f7ed72b071eae9ce99eb48267438e7103f02d637e5be4ff7eed4e6e8376b716",
    ),
    CompletedLowerFactory(
        "prime-field-polynomials",
        "prime_field_polynomial_evaluation_candidate",
        "make_prime_field_polynomial_evaluation_candidate_theorems",
        "prime-field-polynomials-rfc-v1.md",
        37246,
        "9638337f69bdc1f5491255b767dc90042244402e34ceab84902b0481c2eab802",
        18,
        "e9d4a303c1d6863d4e1fc9bfa3321ec2c093d4c5d55b0a5bc6f4e7511302aef2",
    ),
    CompletedLowerFactory(
        "divisor-involutions",
        "divisor_involution_candidate",
        "make_divisor_involution_candidate_theorems",
        "divisor-involution-rfc-v1.md",
        17031,
        "67297015bcfbeb16b9090f537a2771d5c3cbfa4000d5c83c90cd0ba16cb15be7",
        12,
        "c15344f6e8ca8335116cea82dec586421c75f66ff0e9badb06858fda12aee0c6",
    ),
    CompletedLowerFactory(
        "mobius-divisor-cancellation",
        "mobius_divisor_cancellation_candidate",
        "make_mobius_divisor_cancellation_candidate_theorems",
        "mobius-divisor-cancellation-rfc-v1.md",
        46279,
        "9af47fd019e5899586cb02c0e124579d82c4b65d093cfc73d721f411130b457f",
        28,
        "a305d44cc8c8e1274fc7832efb571bacc872ee84cb5f2538fd41cb65c7edfc3b",
    ),
    CompletedLowerFactory(
        "rectangular-sums",
        "signed_rectangular_slice_candidate",
        "make_signed_rectangular_slice_candidate_theorems",
        "signed-rectangular-sums-rfc-v1.md",
        18374,
        "d676600c931936ff00996209c7d744c269427eaf08611fb625e471f608861e5e",
        15,
        "35d897bda49494590b46e309321ac48bc93f33cb2b136520e1595e5cdbaeacce",
    ),
    CompletedLowerFactory(
        "rectangular-sums",
        "signed_rectangular_sums_candidate",
        "make_signed_rectangular_sums_candidate_theorems",
        "signed-rectangular-sums-rfc-v1.md",
        25356,
        "0ce96c5155bb7bf47f5ae2b8151631bd981263f7d05c25f6ec8b3cd365d7a26e",
        17,
        "16a93d17e37749301aebed2254edf2ecd15d924cf9cd2558f30c9604df2fe6a3",
    ),
    CompletedLowerFactory(
        "polynomial-products",
        "prime_field_polynomial_convolution_candidate",
        "make_prime_field_polynomial_convolution_candidate_theorems",
        "prime-field-polynomial-convolution-rfc-v1.md",
        49060,
        "20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24",
        45,
        "fc4d51ed6f083a53de42cd3e003fd83357635740b2cee90e2a79044588fdd5dc",
    ),
    CompletedLowerFactory(
        "polynomial-products",
        "prime_field_polynomial_degree_candidate",
        "make_prime_field_polynomial_degree_candidate_theorems",
        "prime-field-polynomial-convolution-rfc-v1.md",
        12579,
        "3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5",
        8,
        "b00f5d4acff6477bef55226cb27c949d5fddc569a2152c028ae3a4c9bdbf09a8",
    ),
    CompletedLowerFactory(
        "finite-support",
        "signed_finite_support_candidate",
        "make_signed_finite_support_candidate_theorems",
        "signed-finite-support-rfc-v1.md",
        10622,
        "624040e65e0852e652ecda46d2078703e8c0d062dcb06566e24e7d86e9878191",
        8,
        "55874e400c4ecca7dce6e05d5d66e93ef23c091dcf9e8e5ec0a1cc772d9fa5e0",
    ),
    CompletedLowerFactory(
        "dirichlet-convolution",
        "dirichlet_convolution_candidate",
        "make_dirichlet_convolution_candidate_theorems",
        "dirichlet-convolution-rfc-v1.md",
        39272,
        "cec111fbad76f106a5a3f79e2d78fc2a8d483267baa1b19738d4cbfb0c0fb342",
        30,
        "1c87a5bb73650525068f27c1034b2b1ed97ca0023877d23e334c73f925cdce36",
    ),
    CompletedLowerFactory(
        "dirichlet-convolution",
        "dirichlet_commutativity_candidate",
        "make_dirichlet_commutativity_candidate_theorems",
        "dirichlet-convolution-rfc-v1.md",
        14669,
        "1408ca915b4c335afc679b617c4189164b6701730746d3a8aa7f2a260bf75e8d",
        10,
        "85b774007ef1e172aa7dfade6a85c34853f72480a6c550a7b4599286be319c05",
    ),
    CompletedLowerFactory(
        "dirichlet-fubini",
        "dirichlet_fubini_candidate",
        "make_dirichlet_fubini_candidate_theorems",
        "dirichlet-fubini-associativity-rfc-v1.md",
        47311,
        "f18fc61cff3d778568611abebc9698e4c7da9a7dbba37d3b361597dfc988710f",
        29,
        "996506f2707c842ff73c6e0aebc26f5c255d170d167c5db1c94a17d3505da4e5",
    ),
    CompletedLowerFactory(
        "dirichlet-fubini",
        "dirichlet_associativity_candidate",
        "make_dirichlet_associativity_candidate_theorems",
        "dirichlet-fubini-associativity-rfc-v1.md",
        5258,
        "598b0b5658dcba34f97eec4f432de111452ad734a3171832aa2e08bb13a90692",
        3,
        "7d0565b4c8124a3ad8f702fc5a4c647d34e4c7432ecefeceafa71771951f6ab6",
    ),
    CompletedLowerFactory(
        "dirichlet-units",
        "dirichlet_units_candidate",
        "make_dirichlet_units_candidate_theorems",
        "dirichlet-units-rfc-v1.md",
        31264,
        "4821a0e7a8ecac28080db207dd96abf4d02a285a85da6d1173b6a1349a82b77c",
        25,
        "954a654694207db14acb799d843520fb12b3ff2233153b07cadb7bb5c7940911",
    ),
    CompletedLowerFactory(
        "mobius-inversion",
        "mobius_inversion_candidate",
        "make_mobius_inversion_candidate_theorems",
        "mobius-inversion-rfc-v1.md",
        15063,
        "79309dd26c6f434c2e8bb76858dfada758b4a2b489065403b41c70785e1bf183",
        8,
        "4c40808fd2d52ae3feee2f9ab24039f2ae66aa584327c11f8bb2251cab77ef29",
    ),
    CompletedLowerFactory(
        "dirichlet-signed-units",
        "dirichlet_signed_unit_candidate",
        "make_dirichlet_signed_unit_candidate_theorems",
        "dirichlet-signed-unit-rfc-v1.md",
        14597,
        "263ae0497206cee991e34e08f03df3b1922fc4918e67d4d300887aa1ba7de4df",
        9,
        "503e22e4a75aae8b39054144d2d3371f4c8c8f27ac584b18a1383d0e7c9660b7",
    ),
    CompletedLowerFactory(
        "dirichlet-triangular",
        "dirichlet_triangular_candidate",
        "make_dirichlet_triangular_candidate_theorems",
        "dirichlet-triangular-rfc-v1.md",
        17183,
        "5b6e585a4b2df25dee069ddec17e26cddc52c329d45ee7c5fcf307314b10f8ef",
        10,
        "a91a79108e1a636bfdd78a67e3426d33edb2e493be1d43f379aef367db743733",
    ),
    CompletedLowerFactory(
        "dirichlet-inverses",
        "dirichlet_inverse_candidate",
        "make_dirichlet_inverse_candidate_theorems",
        "dirichlet-inverse-rfc-v1.md",
        28549,
        "05347563a82486859a49539e99055504720cc823e14b310389e1d90766a85379",
        21,
        "6ccb0ee24d871bffbdedb3100445411ec03cd1d515586f5b63fa9d4780bfdf20",
    ),
)

COMPLETED_LOWER_FAMILIES = (
    CompletedLowerFamily(
        slug="euler-units",
        generation=170,
        artifact="research/arithmetic-library/artifacts/bottom-layer-euler-units-proof-bundle-v2.json",
        artifact_bytes=571540,
        artifact_sha256="1edfcb7021a0869c2493383c75dea367d757be0b77f36fc6ad3f5fd18ed38210",
        count=32,
        specs_sha256="38ecc1c3c4a6045b7fb301526b09ede9b7927524265909bd59bdbbef1dfaf02e",
        names_sha256="cd20126240c0f26016e1e6952a491db20eaf6759ecb4b795908db05635d30bd3",
        edge_count=91,
        command_count=1203,
        rfc="research/arithmetic-library/euler-units-rfc-v1.md",
        owned_names=("euler_coprime_mod_transport", "euler_multiplier_coprime_iff", "euler_modular_unit_coprime", "euler_coprime_modular_unit", "euler_multiplier_residue_exists", "euler_multiplier_prefix_empty", "euler_multiplier_prefix_extend", "euler_multiplier_prefix_exists", "euler_multiplier_prefix_entry", "euler_multiplier_prefix_bounded_injective", "euler_multiplier_prefix_permutation", "euler_multiplier_permutation_exists", "euler_unit_product_factor_exists", "euler_unit_product_factor_unit_value", "euler_unit_product_factor_nonunit_value", "euler_unit_product_factor_coprime", "euler_unit_product_prefix_empty", "euler_unit_product_prefix_extend", "euler_unit_product_prefix_exists", "euler_unit_product_prefix_drop_last", "euler_unit_product_prefix_entry", "euler_unit_product_coprime", "euler_unit_factor_scaled_congruence", "euler_nonunit_factor_unchanged_congruence", "euler_unit_scaled_prefix_drop_last", "euler_unit_product_reindex_scale", "euler_coprime_weighted_product_cancel", "euler_unit_count_product_balance", "euler_coprime_totient_power_value", "euler_coprime_totient_power", "euler_modular_unit_totient_power", "euler_theorem_for_units"),
        principal_roots=("euler_theorem_for_units", "euler_coprime_totient_power"),
        theorem_count=209,
        root_names=("euler_coprime_modular_unit", "euler_theorem_for_units"),
        node_count=210,
        dependency_edges=566,
        bundle_edges=568,
        body_nodes=12452,
        ordered_cone_names_sha256="ea5d85dceb323e36d0c6f7d1bf8b23bd6f758df65cd1aa436d080705a1e610f1",
        complete_non_alpha_specs_sha256="38ecc1c3c4a6045b7fb301526b09ede9b7927524265909bd59bdbbef1dfaf02e",
        modules=("euler_units_residue_candidate", "euler_units_product_candidate", "euler_units_candidate"),
        principal_pins=(("euler_theorem_for_units", "fcfb262cc347ec2cd7624dffba31f9ed519292b3ba5f1669682cee308cbac39d"), ("euler_coprime_totient_power", "4f3533b3d207055a1f56ca77655cf26a381735fa3999f34a0a2c7935a21497e4")),
    ),
    CompletedLowerFamily(
        slug="prime-fields",
        generation=170,
        artifact="research/arithmetic-library/artifacts/bottom-layer-prime-fields-proof-bundle-v1.json",
        artifact_bytes=594304,
        artifact_sha256="688e7141106c19adec6fa52a0ae77af3d389b77df512622adc93bd3b0c7ba04e",
        count=87,
        specs_sha256="2d007091fb22e1d6c78896feea9363526196ecbcc075d46b0968b372ae39f50b",
        names_sha256="bed3bd851257f868c2b99c8cb6a995fa2fa6e4375257d38471aaec093db361b1",
        edge_count=254,
        command_count=3160,
        rfc="research/arithmetic-library/prime-field-arithmetic-rfc-v1.md",
        owned_names=("prime_field_mod_of_equal", "prime_field_zero_below_prime", "prime_field_residue_reflexive", "prime_field_residue_input_equal", "prime_field_residue_congruence_transport", "prime_field_residue_bounded_value", "prime_field_residue_modulus_zero", "prime_field_add_exists", "prime_field_add_functional", "prime_field_add_exists_unique", "prime_field_add_commutative", "prime_field_multiply_exists", "prime_field_multiply_functional", "prime_field_multiply_exists_unique", "prime_field_multiply_commutative", "prime_field_add_associative", "prime_field_multiply_associative", "prime_field_left_distributive", "prime_field_right_distributive", "prime_field_add_zero_right", "prime_field_add_zero_left", "prime_field_multiply_one_right", "prime_field_multiply_one_left", "prime_field_multiply_zero_right", "prime_field_multiply_zero_left", "prime_field_add_cancel_left", "prime_field_negate_exists", "prime_field_negate_functional", "prime_field_negate_exists_unique", "prime_field_inverse_exists", "prime_field_inverse_functional", "prime_field_inverse_exists_unique", "prime_field_zero_has_no_multiplicative_inverse", "prime_field_inverse_output_nonzero", "prime_field_inverse_symmetric", "prime_field_nonzero_coprime", "prime_field_multiply_cancel_nonzero_left", "prime_field_no_zero_divisors", "prime_field_residue_add", "prime_field_residue_multiply", "prime_field_positive_below_modulus_not_zero", "prime_field_arithmetic_laws", "prime_field_add_grid_value_exists", "prime_field_multiply_grid_value_exists", "prime_field_zero_extended_inverse_exists", "prime_field_zero_extended_inverse_functional", "prime_field_add_prefix_choice", "prime_field_multiply_prefix_choice", "prime_field_negate_prefix_choice", "prime_field_inverse_prefix_choice", "prime_field_add_table_exists", "prime_field_multiply_table_exists", "prime_field_negate_table_exists", "prime_field_inverse_table_exists", "prime_field_operation_tables_exists", "prime_field_add_grid_value_lookup", "prime_field_add_table_lookup", "prime_field_add_table_reflect", "prime_field_multiply_grid_value_lookup", "prime_field_multiply_table_lookup", "prime_field_multiply_table_reflect", "prime_field_negate_table_lookup", "prime_field_negate_table_reflect", "prime_field_inverse_table_lookup", "prime_field_inverse_table_reflect", "prime_field_add_table_commutative", "prime_field_add_table_associative", "prime_field_multiply_table_commutative", "prime_field_multiply_table_associative", "prime_field_inverse_table_zero", "prime_field_inverse_table_nonzero", "prime_field_left_table_distributive", "prime_field_right_table_distributive", "prime_field_enumeration_value", "prime_field_enumeration_is_bijection", "prime_field_cardinality_exists", "prime_field_unit_trace_recode", "prime_field_unit_trace_successor", "prime_field_unit_trace_residue", "prime_field_unit_trace_result_bounded", "prime_field_unit_trace_exists", "prime_field_unit_multiple_residue", "prime_field_unit_multiple_from_residue", "prime_field_unit_multiple_functional", "prime_field_unit_multiple_exists_unique", "prime_field_characteristic_exact", "prime_field_of_prime_order_exists"),
        principal_roots=("prime_field_of_prime_order_exists",),
        theorem_count=227,
        root_names=("prime_field_residue_congruence_transport", "prime_field_inverse_symmetric", "prime_field_residue_multiply", "prime_field_negate_table_reflect", "prime_field_add_table_commutative", "prime_field_add_table_associative", "prime_field_multiply_table_commutative", "prime_field_multiply_table_associative", "prime_field_inverse_table_zero", "prime_field_inverse_table_nonzero", "prime_field_left_table_distributive", "prime_field_right_table_distributive", "prime_field_unit_multiple_exists_unique", "prime_field_of_prime_order_exists"),
        node_count=228,
        dependency_edges=597,
        bundle_edges=611,
        body_nodes=12012,
        ordered_cone_names_sha256="014a22aafa78bd51b23e9083c1c45e1038ef10eea43c23d96ab142ecec467e50",
        complete_non_alpha_specs_sha256="2d007091fb22e1d6c78896feea9363526196ecbcc075d46b0968b372ae39f50b",
        modules=("prime_field_arithmetic_candidate", "prime_field_tables_candidate", "prime_field_finiteness_candidate"),
        principal_pins=(("prime_field_of_prime_order_exists", "f0a61089155f5bb6cd5e6fa79774756a296253a412e2b131bf8f491e8099b8a7"),),
    ),
    CompletedLowerFamily(
        slug="mobius-values",
        generation=170,
        artifact="research/arithmetic-library/artifacts/bottom-layer-mobius-values-proof-bundle-v1.json",
        artifact_bytes=813004,
        artifact_sha256="041f1a3471002ff3cd5fc3da2a6cc751ad2f4a4458a497b3de2a26276fd314b8",
        count=21,
        specs_sha256="547c6e1da76f74f5329b3cc2e5707584bd2534fece4406d7b3493ef11aaa1291",
        names_sha256="bd03b8b7a07a1fb84279de822e042907ec8f0fe5bf4564c7468d53bc9b208602",
        edge_count=64,
        command_count=660,
        rfc="research/arithmetic-library/mobius-divisor-sum-foundations-rfc-v1.md",
        owned_names=("alternating_signed_unit_exists", "alternating_signed_unit_functional", "alternating_signed_unit_zero", "mobius_prime_factor_count_unique", "mobius_input_positive", "mobius_zero_has_no_value", "mobius_from_prime_square", "mobius_from_squarefree_factor_count", "mobius_value_exists", "mobius_squarefree_evaluation", "mobius_value_functional", "mobius_value_exists_unique", "mobius_one", "mobius_squarefree_divisor", "mobius_prime_squarefree", "mobius_squarefree_fresh_prime_product", "mobius_prime_factor_list_append", "mobius_positive_unit_negates_to_negative_unit", "alternating_signed_unit_successor_negates", "mobius_prime_square_value_zero", "mobius_fresh_prime_negates"),
        principal_roots=("mobius_value_exists_unique", "mobius_fresh_prime_negates"),
        theorem_count=236,
        root_names=("mobius_zero_has_no_value", "mobius_value_exists_unique", "mobius_one", "mobius_squarefree_divisor", "mobius_prime_squarefree", "mobius_fresh_prime_negates"),
        node_count=237,
        dependency_edges=669,
        bundle_edges=675,
        body_nodes=15134,
        ordered_cone_names_sha256="ad02d94b60ba5e54d59f9cbfff2f6c4f35fc86d951da65e47cf89ee830e65163",
        complete_non_alpha_specs_sha256="547c6e1da76f74f5329b3cc2e5707584bd2534fece4406d7b3493ef11aaa1291",
        modules=("mobius_value_candidate", "mobius_prime_step_candidate"),
        principal_pins=(("mobius_value_exists_unique", "eb41094b2ceb2273e89e8966ced4cc921decf56dd6bc6dbcb5349c2087aa1135"), ("mobius_fresh_prime_negates", "2b0116e6d32e45fe7ae5e9a8bd7c11e5f95a88021cd42786276cff6e7ec303d2")),
    ),
    CompletedLowerFamily(
        slug="signed-sums",
        generation=170,
        artifact="research/arithmetic-library/artifacts/bottom-layer-signed-sums-proof-bundle-v1.json",
        artifact_bytes=855381,
        artifact_sha256="35bc01ab3f12cc09a5ed9aa3098225090dcc40ac241f9cbd669f99cef4737e57",
        count=30,
        specs_sha256="ddf5801b9e89a639401d1c95ee3745fb44d17e5c255a2dd11d89f38b9de5b37b",
        names_sha256="b345686528e2c260f41059d26a1d1c314944534cca8fc541877b326f6ea1a90d",
        edge_count=73,
        command_count=1410,
        rfc="research/arithmetic-library/mobius-divisor-sum-foundations-rfc-v1.md",
        owned_names=("divisor_signed_table_at_from_components", "divisor_signed_table_at_to_components", "divisor_signed_table_from_components", "divisor_signed_table_construct", "divisor_signed_table_components", "divisor_signed_table_lookup", "divisor_signed_table_at_functional", "divisor_signed_table_restrict", "divisor_signed_sum_from_components", "divisor_signed_sum_to_components", "divisor_signed_sum_exists_from_components", "divisor_signed_sum_functional", "divisor_signed_sum_empty_value", "divisor_signed_sum_empty_exists", "divisor_signed_balance_negate", "divisor_signed_balance_negate_intro", "divisor_signed_negate_fixed_zero", "divisor_natural_sum_successor_intro", "divisor_signed_table_equality_component_balance", "divisor_signed_sum_extensional", "divisor_signed_sum_negation_transport", "divisor_signed_sum_successor_intro", "divisor_signed_sum_successor_decompose", "divisor_signed_table_lookup_from_components", "divisor_signed_table_reindex_data_exists", "divisor_signed_table_reindex_from_components", "divisor_signed_table_reindex_exists", "divisor_signed_table_reindex_functional", "divisor_signed_sum_component_reindex", "divisor_signed_sum_permutation_invariant"),
        principal_roots=("divisor_signed_table_reindex_exists", "divisor_signed_sum_permutation_invariant"),
        theorem_count=213,
        root_names=("divisor_signed_table_construct", "divisor_signed_table_restrict", "divisor_signed_sum_functional", "divisor_signed_sum_empty_exists", "divisor_signed_balance_negate_intro", "divisor_signed_negate_fixed_zero", "divisor_signed_sum_negation_transport", "divisor_signed_sum_successor_intro", "divisor_signed_sum_successor_decompose", "divisor_signed_table_reindex_exists", "divisor_signed_sum_permutation_invariant"),
        node_count=214,
        dependency_edges=560,
        bundle_edges=571,
        body_nodes=13724,
        ordered_cone_names_sha256="d91e6c3339f7f66a7fcf144a79e58bdcd0c39337f7c0ad860792a0b03c68601f",
        complete_non_alpha_specs_sha256="ddf5801b9e89a639401d1c95ee3745fb44d17e5c255a2dd11d89f38b9de5b37b",
        modules=("divisor_sum_table_candidate", "divisor_sum_algebra_candidate", "divisor_sum_reindex_candidate"),
        principal_pins=(("divisor_signed_table_reindex_exists", "f2cc667b787e62fe9e43a8689834b3edf048e4fe71b615639db1d2062d93f9f9"), ("divisor_signed_sum_permutation_invariant", "0e94ef4db7c6f73d73ae87525d29e24722764adabcd38a908ab3a844bfec57ac")),
    ),
    CompletedLowerFamily(
        slug="divisor-sums",
        generation=126,
        artifact="research/arithmetic-library/artifacts/lower-tier-divisor-sums-proof-bundle-v1.json",
        artifact_bytes=1841261,
        artifact_sha256="96740bcedad194ebed5066ae03fa20cd922e702ae925b2c85f4ed45649aa0307",
        count=37,
        specs_sha256="9bfd07e098154dd119b767459f69f8670151b4acd5c3ab0fc3813a987b704870",
        names_sha256="ae8fb6562e9f2ee88b0996a6d8887013f714732d02728daff85ee37ca289f6af",
        edge_count=92,
        command_count=1380,
        rfc="research/arithmetic-library/mobius-tables-divisor-sums-rfc-v1.md",
        owned_names=("arithmetic_signed_table_component_prefix_preserved", "arithmetic_signed_table_equal_entry_transport", "arithmetic_signed_table_extend_at", "arithmetic_signed_table_append", "arithmetic_signed_table_singleton", "arithmetic_signed_sum_exists", "arithmetic_signed_sum_append_transport", "mobius_table_zero_constructor", "mobius_table_append", "mobius_table_exists", "mobius_table_lookup", "mobius_table_entry_iff", "mobius_table_one_entry", "mobius_table_extensional", "mobius_table_restrict", "divisor_mask_entry_zero", "divisor_mask_entry_from_quotient", "divisor_mask_entry_from_nondivisor", "divisor_mask_entry_exists", "divisor_mask_entry_functional", "divisor_mask_entry_quotient_input", "divisor_mask_entry_omitted_value", "divisor_mask_prefix_zero_constructor", "divisor_mask_prefix_append", "divisor_mask_prefix_exists", "divisor_mask_prefix_extensional", "divisor_mask_prefix_restrict", "divisor_mask_positive_quotient_entry", "divisor_mask_omitted_entry", "divisor_mask_entry_positive_source_extensional", "divisor_mask_positive_source_extensional", "signed_divisor_sum_exists", "signed_divisor_sum_functional", "signed_divisor_sum_exists_unique", "signed_divisor_sum_zero_excluded", "signed_divisor_sum_one", "signed_divisor_sum_positive_source_extensional"),
        principal_roots=("mobius_table_exists", "signed_divisor_sum_positive_source_extensional", "signed_divisor_sum_exists_unique"),
        theorem_count=314,
        root_names=("arithmetic_signed_sum_append_transport", "mobius_table_exists", "mobius_table_one_entry", "mobius_table_extensional", "mobius_table_restrict", "divisor_mask_entry_quotient_input", "divisor_mask_prefix_restrict", "signed_divisor_sum_exists_unique", "signed_divisor_sum_zero_excluded", "signed_divisor_sum_one", "signed_divisor_sum_positive_source_extensional"),
        node_count=315,
        dependency_edges=864,
        bundle_edges=875,
        body_nodes=20685,
        ordered_cone_names_sha256="69f8de6dc63e249c3289ede400f875c9ab68cc3aaac0ac847d5d0501f651ccd4",
        complete_non_alpha_specs_sha256="bc820d7e1561fc7bb8916fb222b62ed7d315e9633431807bda3f8bbd7dd386ef",
        modules=("arithmetic_table_extension_candidate", "mobius_table_candidate", "divisor_mask_candidate"),
        principal_pins=(("mobius_table_exists", "9d90a11bd987bfe516272671293b30a0d264fe613d2632c628b5701634cf5dd3"), ("signed_divisor_sum_positive_source_extensional", "5db775338790a36cdffa83a65f52f26d244827ba90942feb09600b9f5a202672"), ("signed_divisor_sum_exists_unique", "c148a766390471cd871ca467503a9a7c380142964aff8830ca412a20f743ba6d")),
    ),
    CompletedLowerFamily(
        slug="signed-weighted-sums",
        generation=126,
        artifact="research/arithmetic-library/artifacts/lower-tier-signed-weighted-sums-proof-bundle-v1.json",
        artifact_bytes=2293317,
        artifact_sha256="e88ddec495a71d673e670299ea3943a5a996eecb1296fb746e107c8e0b81c967",
        count=40,
        specs_sha256="d1e23134d7f367d169f181c67939df5548101c83e9a73da43544c49e96590fae",
        names_sha256="508f9c9dfde41f64ade7fa5fd2a6ca673fd7c8ca226655e1aa4dea98c4f3439c",
        edge_count=121,
        command_count=2117,
        rfc="research/arithmetic-library/signed-weighted-sums-rfc-v1.md",
        owned_names=("signed_table_domain_resize", "signed_table_lookup_any", "signed_table_add_lookup", "signed_table_add_restrict", "signed_table_add_empty", "signed_table_add_extensional_unique", "signed_table_multiply_lookup", "signed_table_multiply_restrict", "signed_table_multiply_empty", "signed_table_multiply_extensional_unique", "signed_table_scalar_lookup", "signed_table_scalar_restrict", "signed_table_scalar_empty", "signed_table_scalar_extensional_unique", "signed_table_add_extend", "signed_table_add_exists", "signed_table_add_exists_extensionally_unique", "signed_table_multiply_extend", "signed_table_multiply_exists", "signed_table_multiply_exists_extensionally_unique", "signed_table_scalar_extend", "signed_table_scalar_exists", "signed_table_scalar_exists_extensionally_unique", "signed_table_add_reassociate", "signed_table_add_medial", "signed_table_scalar_add_intro", "signed_prefix_sum_pointwise_add", "signed_prefix_sum_scalar_multiply", "signed_prefix_sum_pointwise_add_values_exist", "signed_prefix_sum_scalar_multiply_values_exist", "signed_weighted_sum_exists", "signed_weighted_sum_functional", "signed_weighted_sum_exists_unique", "signed_weighted_sum_empty_value", "signed_weighted_sum_empty_exists", "signed_table_weighted_add_distributive", "signed_weighted_scalar_commute", "signed_table_weighted_scalar_commute", "signed_weighted_sum_add_linearity", "signed_weighted_sum_scalar_linearity"),
        principal_roots=("signed_weighted_sum_exists_unique", "signed_weighted_sum_scalar_linearity", "signed_weighted_sum_add_linearity"),
        theorem_count=226,
        root_names=("signed_table_multiply_restrict", "signed_table_add_exists_extensionally_unique", "signed_table_multiply_exists_extensionally_unique", "signed_table_scalar_exists_extensionally_unique", "signed_prefix_sum_pointwise_add_values_exist", "signed_prefix_sum_scalar_multiply_values_exist", "signed_weighted_sum_exists_unique", "signed_weighted_sum_empty_exists", "signed_weighted_sum_add_linearity", "signed_weighted_sum_scalar_linearity"),
        node_count=227,
        dependency_edges=574,
        bundle_edges=584,
        body_nodes=13692,
        ordered_cone_names_sha256="fc0b542095cac19507490ca5a732b7941f8381cd30be7bcf09eb698bf3a29986",
        complete_non_alpha_specs_sha256="c6546860fac1a31e7e248bbd362a83d4d2f9cf26e1f8f9d9036286cebdf59f0e",
        modules=("signed_table_operations_candidate", "signed_sum_linearity_candidate", "signed_weighted_sum_candidate"),
        principal_pins=(("signed_weighted_sum_exists_unique", "1ed794504914ee8304903be9fce6c08e5e310c7b0e75c244382438433c4c3f14"), ("signed_weighted_sum_scalar_linearity", "488852252ab9e41daf5e2e6e234f8a9e046042f269dd9f5fd1bd9a074c45cbeb"), ("signed_weighted_sum_add_linearity", "0515fa77e429a50f266b273b77efa2682ec7cc78c3e30948559d6a5c3363f255")),
    ),
    CompletedLowerFamily(
        slug="prime-field-polynomials",
        generation=126,
        artifact="research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json",
        artifact_bytes=688987,
        artifact_sha256="6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a",
        count=49,
        specs_sha256="0ff662d165003510ed2cd20d724762d9d4166e62cd67e361073e7e15bc5fcd8b",
        names_sha256="1657e984d7cd41d0bd36458fc043e00f65af437c8228a2e118eeed014c69fa9b",
        edge_count=131,
        command_count=2829,
        rfc="research/arithmetic-library/prime-field-polynomials-rfc-v1.md",
        owned_names=("prime_field_polynomial_normalization_from_division", "prime_field_polynomial_normalization_exists", "prime_field_polynomial_normalization_entry", "prime_field_polynomial_normalization_bounded", "prime_field_polynomial_normalization_functional", "prime_field_polynomial_normalization_reflexive", "prime_field_polynomial_normalization_transport", "prime_field_polynomial_normalization_idempotent", "prime_field_polynomial_repeat_coefficients", "prime_field_polynomial_repeat_exists", "prime_field_polynomial_zero_exists", "prime_field_polynomial_add_from_normalization", "prime_field_polynomial_add_exists", "prime_field_polynomial_add_entry", "prime_field_polynomial_add_bounded", "prime_field_polynomial_add_functional", "prime_field_polynomial_add_transport", "prime_field_polynomial_add_commutative", "prime_field_polynomial_add_zero_right", "prime_field_polynomial_scale_from_normalization", "prime_field_polynomial_scale_exists", "prime_field_polynomial_scale_entry", "prime_field_polynomial_scale_bounded", "prime_field_polynomial_scale_functional", "prime_field_polynomial_scale_transport", "prime_field_polynomial_scale_one", "prime_field_polynomial_scale_zero", "prime_field_polynomial_add_associative", "prime_field_polynomial_scale_associative", "prime_field_polynomial_scale_distributes_over_add", "prime_field_polynomial_scalar_add_distributes", "prime_field_polynomial_horner_canonical_step", "prime_field_polynomial_horner_trace_from_normalization", "prime_field_polynomial_horner_exists", "prime_field_polynomial_horner_input_bounds", "prime_field_polynomial_horner_empty", "prime_field_polynomial_horner_successor_decompose", "prime_field_polynomial_horner_transport", "prime_field_polynomial_horner_normalization_residue", "prime_field_polynomial_horner_residue", "prime_field_polynomial_horner_functional", "prime_field_polynomial_horner_exists_unique", "prime_field_polynomial_horner_empty_construct", "prime_field_polynomial_horner_successor_construct", "prime_field_polynomial_horner_constant", "prime_field_polynomial_horner_zero", "prime_field_polynomial_normalized_horner_iff", "prime_field_polynomial_horner_result_bounded", "prime_field_polynomial_reduce_and_evaluate_exists"),
        principal_roots=("prime_field_polynomial_horner_exists_unique", "prime_field_polynomial_normalized_horner_iff", "prime_field_polynomial_reduce_and_evaluate_exists"),
        theorem_count=201,
        root_names=("prime_field_polynomial_normalization_transport", "prime_field_polynomial_normalization_idempotent", "prime_field_polynomial_zero_exists", "prime_field_polynomial_add_exists", "prime_field_polynomial_add_bounded", "prime_field_polynomial_add_functional", "prime_field_polynomial_add_transport", "prime_field_polynomial_add_commutative", "prime_field_polynomial_add_zero_right", "prime_field_polynomial_scale_exists", "prime_field_polynomial_scale_bounded", "prime_field_polynomial_scale_functional", "prime_field_polynomial_scale_transport", "prime_field_polynomial_scale_one", "prime_field_polynomial_scale_zero", "prime_field_polynomial_add_associative", "prime_field_polynomial_scale_associative", "prime_field_polynomial_scale_distributes_over_add", "prime_field_polynomial_scalar_add_distributes", "prime_field_polynomial_horner_transport", "prime_field_polynomial_horner_exists_unique", "prime_field_polynomial_horner_constant", "prime_field_polynomial_horner_zero", "prime_field_polynomial_normalized_horner_iff", "prime_field_polynomial_horner_result_bounded", "prime_field_polynomial_reduce_and_evaluate_exists"),
        node_count=202,
        dependency_edges=493,
        bundle_edges=519,
        body_nodes=11889,
        ordered_cone_names_sha256="194c347a6e3ecf3a4392cb5fa234ef4e2b46129c5381d27cbaaa104b6ea836f8",
        complete_non_alpha_specs_sha256="2c9acf7b60877733669e07560e670111754c34ceb361441befc55bb034bf3dff",
        modules=("prime_field_polynomial_candidate", "prime_field_polynomial_evaluation_candidate"),
        principal_pins=(("prime_field_polynomial_horner_exists_unique", "b4e5a2cd91b33b7366aa11d591d5da743acdb244348f438797daf1be243c3941"), ("prime_field_polynomial_normalized_horner_iff", "fbed602c60a29f5b4474d678ccd397c2ff5d50e7fb52f06480c26e1938a762e5"), ("prime_field_polynomial_reduce_and_evaluate_exists", "2f0d67795bf12542c6c9fb48cb4d63d26213e8e090bbca1a7a89257a49dd0e2c")),
    ),
    CompletedLowerFamily(
        slug="divisor-involutions",
        generation=125,
        artifact="research/arithmetic-library/artifacts/lower-continuation-divisor-involutions-proof-bundle-v1.json",
        artifact_bytes=292245,
        artifact_sha256="deffb1e384e64cd2cb56b4c1603a0fdde7578cec15e80618f5b06197fabf6fed",
        count=12,
        specs_sha256="c15344f6e8ca8335116cea82dec586421c75f66ff0e9badb06858fda12aee0c6",
        names_sha256="078bb720ba7af1a3bf09c30b252c4f8c8b4bbcdc7494d40f43d6235348abd0ee",
        edge_count=34,
        command_count=480,
        rfc="research/arithmetic-library/divisor-involution-rfc-v1.md",
        owned_names=("positive_divisor_quotient_exists_unique", "divisor_complement_exists", "divisor_complement_functional", "divisor_complement_positive_equation", "divisor_complement_symmetric", "divisor_complement_bounded", "divisor_complement_prefix_exists", "divisor_complement_prefix_lookup", "divisor_complement_prefix_permutation", "positive_divisor_involution_exists", "divisor_complement_prefix_involution", "divisor_complement_prefix_positive_quotient"),
        principal_roots=("positive_divisor_quotient_exists_unique", "positive_divisor_involution_exists", "divisor_complement_prefix_involution"),
        theorem_count=139,
        root_names=("positive_divisor_quotient_exists_unique", "divisor_complement_positive_equation", "positive_divisor_involution_exists", "divisor_complement_prefix_involution", "divisor_complement_prefix_positive_quotient"),
        node_count=140,
        dependency_edges=350,
        bundle_edges=355,
        body_nodes=7711,
        ordered_cone_names_sha256="6c3e1a91340b5c26c68fab35e0f86c53959e36a00312151dcc32b4d3fae0cf98",
        complete_non_alpha_specs_sha256="c15344f6e8ca8335116cea82dec586421c75f66ff0e9badb06858fda12aee0c6",
        modules=("divisor_involution_candidate",),
        principal_pins=(("positive_divisor_quotient_exists_unique", "a02a6f2e061e89191c7e4dff86b60611ebf035717468a17707bf5537486da384"), ("positive_divisor_involution_exists", "7fff4b15206b4bc27488134518c5e8231aee964a484e515576a6426be170719d"), ("divisor_complement_prefix_involution", "24bdefde49ebf80220bf5c974be3261d250dc98472d1228f6f3484492a9f34c1")),
    ),
    CompletedLowerFamily(
        slug="mobius-divisor-cancellation",
        generation=125,
        artifact="research/arithmetic-library/artifacts/lower-continuation-mobius-divisor-cancellation-proof-bundle-v1.json",
        artifact_bytes=2498683,
        artifact_sha256="f858f6bd9e09d6ec33b48689b385222153ad9d326eccb8239ac5776b39955542",
        count=28,
        specs_sha256="a305d44cc8c8e1274fc7832efb571bacc872ee84cb5f2538fd41cb65c7edfc3b",
        names_sha256="d749efdf6c502e97a463e462670c3a55b00636fad75b650371bdc53c1ea00534",
        edge_count=99,
        command_count=1569,
        rfc="research/arithmetic-library/mobius-divisor-cancellation-rfc-v1.md",
        owned_names=("prime_toggle_square_quotient_divides", "prime_toggle_fresh_divisor_product", "prime_factor_toggle_exists", "prime_factor_toggle_functional", "prime_factor_toggle_symmetric", "prime_factor_toggle_positive", "prime_factor_toggle_preserves_divisor", "divisor_prime_toggle_exists", "divisor_prime_toggle_functional", "divisor_prime_toggle_symmetric", "divisor_prime_toggle_bounded", "divisor_prime_toggle_prefix_exists", "divisor_prime_toggle_prefix_lookup", "divisor_prime_toggle_prefix_permutation", "divisor_prime_toggle_permutation_exists", "mobius_prime_factor_toggle_negates", "mobius_divisor_mask_actual_value", "mobius_divisor_mask_prime_toggle_negates", "signed_table_swapped_components_negation_at", "signed_prefix_sum_pointwise_negate", "anti_invariant_signed_permutation_sum_zero", "mobius_divisor_mask_prime_factor_sum_zero", "mobius_divisor_sum_nonunit_value_zero", "mobius_divisor_sum_nonunit_zero", "mobius_divisor_sum_unit_one", "mobius_divisor_sum_cancellation", "mobius_divisor_sum_cancellation_exists", "mobius_divisor_sum_cancellation_on_positive_values"),
        principal_roots=("mobius_divisor_sum_cancellation", "mobius_divisor_sum_cancellation_exists", "mobius_divisor_sum_cancellation_on_positive_values"),
        theorem_count=376,
        root_names=("mobius_divisor_sum_cancellation_exists", "mobius_divisor_sum_cancellation_on_positive_values"),
        node_count=377,
        dependency_edges=1079,
        bundle_edges=1081,
        body_nodes=27012,
        ordered_cone_names_sha256="e95bcecd37682754823dfb741006d435529470546b52470aff546b574c8967ff",
        complete_non_alpha_specs_sha256="2be1ed09952bfbcdad0fb206ff08fb1faa54b3984f5e2cd507031eff08f7632e",
        modules=("mobius_divisor_cancellation_candidate",),
        principal_pins=(("mobius_divisor_sum_cancellation", "dc605f677a0cdb931e7f3e65b29569dea83f1b9db136b932913a1936dc2b3406"), ("mobius_divisor_sum_cancellation_exists", "50bcf039c53ca70483eadd8ff3f9c3baf484d1fc82f84afe21009620ff674280"), ("mobius_divisor_sum_cancellation_on_positive_values", "be20bbedecba3566c7d3611f121e3d2e4fdaffd7fdee715dcd7e60afdb4cfd56")),
    ),
    CompletedLowerFamily(
        slug="rectangular-sums",
        generation=125,
        artifact="research/arithmetic-library/artifacts/lower-continuation-rectangular-sums-proof-bundle-v1.json",
        artifact_bytes=2151122,
        artifact_sha256="a6f62d8a0c89431b3596a0d15278643da6981afe166107cdc6aefa5433485395",
        count=32,
        specs_sha256="3f774e07d82400c19850521fae1779bc363aff5e56bb32cbc1042a5d3dd4403d",
        names_sha256="83e70a5b157fded2c2ec78b7c2dbc57779b622ace39eff51c6e09d34c12024c8",
        edge_count=92,
        command_count=1393,
        rfc="research/arithmetic-library/signed-rectangular-sums-rfc-v1.md",
        owned_names=("signed_rectangular_slice_lookup", "signed_rectangular_slice_restrict", "signed_rectangular_slice_empty", "signed_rectangular_slice_extensional_unique", "signed_rectangular_slice_extend", "signed_rectangular_slice_exists", "signed_rectangular_slice_exists_extensionally_unique", "signed_rectangular_slice_sum_exists", "signed_rectangular_slice_sum_functional", "signed_rectangular_slice_sum_empty_value", "signed_rectangular_slice_sum_empty_exists", "signed_rectangular_slice_sum_successor_decompose", "signed_rectangular_slice_sum_successor_intro", "signed_rectangular_slice_sum_successor_add", "signed_rectangular_slice_sum_exists_unique", "signed_rectangular_row_sums_lookup", "signed_rectangular_row_sums_restrict_outer", "signed_rectangular_row_sums_empty", "signed_rectangular_row_sums_extensional_unique", "signed_rectangular_row_sums_extend", "signed_rectangular_row_sums_exists", "signed_rectangular_row_sums_exists_extensionally_unique", "signed_rectangular_sum_exists", "signed_rectangular_sum_functional", "signed_rectangular_sum_exists_unique", "signed_rectangular_sum_zero_outer", "signed_rectangular_row_sums_zero_inner", "signed_rectangular_sum_zero_inner", "signed_rectangular_columns_successor_add", "signed_rectangular_fubini", "signed_rectangular_fubini_exists", "signed_rectangular_row_major_fubini"),
        principal_roots=("signed_rectangular_slice_exists_extensionally_unique", "signed_rectangular_fubini", "signed_rectangular_row_major_fubini"),
        theorem_count=216,
        root_names=("signed_rectangular_slice_exists_extensionally_unique", "signed_rectangular_slice_sum_empty_exists", "signed_rectangular_slice_sum_successor_decompose", "signed_rectangular_slice_sum_exists_unique", "signed_rectangular_row_sums_exists_extensionally_unique", "signed_rectangular_sum_exists_unique", "signed_rectangular_row_major_fubini"),
        node_count=217,
        dependency_edges=544,
        bundle_edges=551,
        body_nodes=12534,
        ordered_cone_names_sha256="112c65f2294d5e54c697636fd89c39b3a7fb5d3d344783aff08972af0b1afc13",
        complete_non_alpha_specs_sha256="b3268079729a43f3edb77867b94feeb4918c6a40caa90a6b5ee7dc3ae36c7a16",
        modules=("signed_rectangular_slice_candidate", "signed_rectangular_sums_candidate"),
        principal_pins=(("signed_rectangular_slice_exists_extensionally_unique", "d0fbe7f70725333cc208f00e860d04886fafdc5fef4a36bc6e811dd88391ddd4"), ("signed_rectangular_fubini", "74787482d51c759b2472790323be3c54494bbf97fab08de48afce458898fd14d"), ("signed_rectangular_row_major_fubini", "df286640d573e43c4ce8fc84ed9a405eb4568577f4f683001adb7ae8324ff3ec")),
    ),
    CompletedLowerFamily(
        slug="polynomial-products",
        generation=125,
        artifact="research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json",
        artifact_bytes=745307,
        artifact_sha256="55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3",
        count=53,
        specs_sha256="4ee9ff43d58fac794947ac67349efd966b78472b2f9777c16fe222e5ca194eaa",
        names_sha256="67a5ca213e79b42852e3579d12c012b4e44f5b605a029e77f3ebb9f63768ecf5",
        edge_count=123,
        command_count=2496,
        rfc="research/arithmetic-library/prime-field-polynomial-convolution-rfc-v1.md",
        owned_names=("polynomial_zero_extended_entry_exists", "polynomial_zero_extended_entry_functional", "polynomial_zero_extended_entry_inside", "polynomial_zero_extended_entry_transport", "polynomial_zero_extended_zero_value", "polynomial_diagonal_term_exists", "polynomial_diagonal_term_functional", "polynomial_diagonal_term_transport", "polynomial_diagonal_term_leading", "polynomial_diagonal_term_zero_left", "polynomial_diagonal_term_zero_right", "polynomial_diagonal_term_past_support", "polynomial_diagonal_prefix_entry", "polynomial_diagonal_prefix_recoding", "polynomial_diagonal_prefix_from_pointwise", "polynomial_diagonal_prefix_functional", "polynomial_diagonal_prefix_exists", "polynomial_diagonal_prefix_input_transport", "prime_field_convolution_coefficient_exists", "prime_field_convolution_coefficient_functional", "prime_field_convolution_coefficient_bounded", "prime_field_convolution_coefficient_transport", "prime_field_convolution_coefficient_leading", "prime_field_convolution_coefficient_zero_left", "prime_field_convolution_coefficient_zero_right", "prime_field_convolution_coefficient_zero_past_support", "prime_field_convolution_prefix_entry", "prime_field_convolution_prefix_recoding", "prime_field_convolution_prefix_from_pointwise", "prime_field_convolution_prefix_functional", "prime_field_convolution_prefix_exists", "prime_field_convolution_prefix_bounded", "prime_field_convolution_prefix_input_transport", "polynomial_product_length_exists", "polynomial_product_length_functional", "prime_field_polynomial_convolution_bounded", "prime_field_polynomial_convolution_entry", "prime_field_polynomial_convolution_transport", "prime_field_polynomial_convolution_functional", "prime_field_polynomial_convolution_at_length_exists", "prime_field_polynomial_convolution_exists_unique", "prime_field_polynomial_convolution_empty", "prime_field_polynomial_convolution_zero_left", "prime_field_polynomial_convolution_zero_right", "prime_field_polynomial_convolution_outside_zero", "polynomial_product_length_positive_inputs", "prime_field_polynomial_represented_degree_leading_nonzero", "prime_field_polynomial_represented_degree_transport", "prime_field_polynomial_represented_degree_excludes_zero", "prime_field_polynomial_monic_degree_examples", "prime_field_polynomial_convolution_leading_coefficient", "prime_field_polynomial_convolution_represented_degree", "prime_field_polynomial_convolution_represented_degree_exists"),
        principal_roots=("prime_field_polynomial_convolution_exists_unique", "prime_field_polynomial_convolution_outside_zero", "prime_field_polynomial_convolution_represented_degree_exists"),
        theorem_count=209,
        root_names=("polynomial_zero_extended_entry_inside", "polynomial_diagonal_prefix_recoding", "prime_field_polynomial_convolution_transport", "prime_field_polynomial_convolution_exists_unique", "prime_field_polynomial_convolution_empty", "prime_field_polynomial_convolution_zero_left", "prime_field_polynomial_convolution_zero_right", "prime_field_polynomial_convolution_outside_zero", "prime_field_polynomial_represented_degree_leading_nonzero", "prime_field_polynomial_represented_degree_transport", "prime_field_polynomial_represented_degree_excludes_zero", "prime_field_polynomial_monic_degree_examples", "prime_field_polynomial_convolution_represented_degree_exists"),
        node_count=210,
        dependency_edges=490,
        bundle_edges=503,
        body_nodes=11604,
        ordered_cone_names_sha256="7b21fab5ca61214a7a5630eda76a965017059d8ebfb1987319281ed0c73fc679",
        complete_non_alpha_specs_sha256="109d0194057f4b216d9f2717a475fa22d3c39c882a6d724cf0b1d1957b6d0103",
        modules=("prime_field_polynomial_convolution_candidate", "prime_field_polynomial_degree_candidate"),
        principal_pins=(("prime_field_polynomial_convolution_exists_unique", "68befd01e16fc6522f2c848ddaac2bef81ead256b41bf6b03fbff132b7693410"), ("prime_field_polynomial_convolution_outside_zero", "724cc30193c104f03c1777ace6bec5f40681be6436e7da9f165d44d10cb97501"), ("prime_field_polynomial_convolution_represented_degree_exists", "8ff4406ec7462fc8e97a47932550abde9c428392cda01a1c86fe2dfd082fc51a")),
    ),
    CompletedLowerFamily(
        slug="finite-support",
        generation=113,
        artifact="research/arithmetic-library/artifacts/dirichlet-finite-support-proof-bundle-v1.json",
        artifact_bytes=587407,
        artifact_sha256="99d889c64fb066f79247afa4310e0143f42bfffbc2cf56e4bd9be3735e0cac47",
        count=8,
        specs_sha256="55874e400c4ecca7dce6e05d5d66e93ef23c091dcf9e8e5ec0a1cc772d9fa5e0",
        names_sha256="95ec8fdb5146fe8ca849860dc675e6145b8d3932fa658490e1c60079d785aefb",
        edge_count=25,
        command_count=312,
        rfc="research/arithmetic-library/signed-finite-support-rfc-v1.md",
        owned_names=("signed_zero_window_empty", "signed_zero_window_restrict", "signed_zero_window_raise_lower", "signed_prefix_sum_zero_tail", "signed_prefix_sum_zero_value", "signed_prefix_sum_zero_exists", "signed_prefix_sum_last_value", "signed_prefix_sum_zero_padding_iff"),
        principal_roots=("signed_prefix_sum_zero_tail", "signed_prefix_sum_last_value", "signed_prefix_sum_zero_padding_iff"),
        theorem_count=169,
        root_names=("signed_zero_window_empty", "signed_zero_window_raise_lower", "signed_prefix_sum_zero_exists", "signed_prefix_sum_last_value", "signed_prefix_sum_zero_padding_iff"),
        node_count=170,
        dependency_edges=392,
        bundle_edges=397,
        body_nodes=8697,
        ordered_cone_names_sha256="03c8d338c792308a4ca0058cca0e0d93571cc79aea8acc2385a6d818f98a43e7",
        complete_non_alpha_specs_sha256="bc7cc71f059f01879f0f4812014a30cb0a720f5e8769215a3d923186847a4b9d",
        modules=("signed_finite_support_candidate",),
        principal_pins=(("signed_prefix_sum_zero_tail", "ae30d900f38f2fa5e22a59fe2a38056ffb4242b1fcb8ebf364c7673606f1d46b"), ("signed_prefix_sum_last_value", "d813ceef952a622bca2fb25909b732dc7c4f9987720b050a3c5a41b590690013"), ("signed_prefix_sum_zero_padding_iff", "0a6919b464fecaa0138aef0d8ce9f24d3e2f48357a29544523c17e67b3200f4e")),
    ),
    CompletedLowerFamily(
        slug="dirichlet-convolution",
        generation=113,
        artifact="research/arithmetic-library/artifacts/dirichlet-convolution-proof-bundle-v1.json",
        artifact_bytes=2756953,
        artifact_sha256="313316e788a10dc281dfb0541a447bad9b7b26bbbd68b1030db89d8d28c5a38b",
        count=40,
        specs_sha256="8780d9e343234b030e0cd2de518df0ddd9c5c5b4bee89eb00251f770d3ff29ce",
        names_sha256="8cea5b0d22089b282c837358d0650e5e9ecea62a05854b127d859caa08a15ddf",
        edge_count=102,
        command_count=1754,
        rfc="research/arithmetic-library/dirichlet-convolution-rfc-v1.md",
        owned_names=("dirichlet_convolution_entry_zero", "dirichlet_convolution_entry_from_quotient", "dirichlet_convolution_entry_from_nondivisor", "dirichlet_convolution_entry_omitted_value", "dirichlet_convolution_entry_quotient_product", "dirichlet_convolution_entry_functional", "dirichlet_convolution_entry_exists", "dirichlet_convolution_prefix_zero_constructor", "dirichlet_convolution_prefix_append", "dirichlet_convolution_prefix_exists", "dirichlet_convolution_prefix_lookup", "dirichlet_convolution_prefix_extensional", "dirichlet_convolution_prefix_restrict", "dirichlet_convolution_prefix_quotient_entry", "dirichlet_convolution_prefix_omitted_entry", "dirichlet_convolution_sum_exists", "dirichlet_convolution_sum_functional", "dirichlet_convolution_sum_exists_unique", "dirichlet_convolution_sum_zero_excluded", "dirichlet_convolution_entry_positive_source_extensional", "dirichlet_convolution_prefix_positive_source_extensional", "dirichlet_convolution_positive_source_extensional", "dirichlet_convolution_positive_source_transport", "dirichlet_convolution_table_zero_constructor", "dirichlet_convolution_table_append", "dirichlet_convolution_table_exists", "dirichlet_convolution_table_lookup", "dirichlet_convolution_table_extensional", "dirichlet_convolution_table_exists_extensionally_unique", "dirichlet_convolution_table_restrict", "dirichlet_convolution_entry_complement", "dirichlet_convolution_prefix_value_from_entry", "dirichlet_convolution_prefix_complement_reindex", "dirichlet_convolution_sum_commutative", "dirichlet_convolution_sum_swap", "dirichlet_convolution_table_commutative", "dirichlet_convolution_entry_past_support_zero", "dirichlet_convolution_prefix_zero_tail", "dirichlet_convolution_from_padded_prefix", "dirichlet_convolution_padded_prefix_iff"),
        principal_roots=("dirichlet_convolution_table_exists_extensionally_unique", "dirichlet_convolution_table_commutative", "dirichlet_convolution_padded_prefix_iff"),
        theorem_count=269,
        root_names=("dirichlet_convolution_prefix_quotient_entry", "dirichlet_convolution_prefix_omitted_entry", "dirichlet_convolution_sum_exists_unique", "dirichlet_convolution_sum_zero_excluded", "dirichlet_convolution_positive_source_transport", "dirichlet_convolution_table_lookup", "dirichlet_convolution_table_exists_extensionally_unique", "dirichlet_convolution_table_restrict", "dirichlet_convolution_table_commutative", "dirichlet_convolution_padded_prefix_iff"),
        node_count=270,
        dependency_edges=702,
        bundle_edges=712,
        body_nodes=18180,
        ordered_cone_names_sha256="08e991d3d5fac42651eaf430f404c5b72f606a71d9a0e6373a66a7f432d4f17c",
        complete_non_alpha_specs_sha256="6c9b3862e13fad0a63630a3bae3a1244b6dcddbdafb418a787668767a4baf129",
        modules=("dirichlet_convolution_candidate", "dirichlet_commutativity_candidate"),
        principal_pins=(("dirichlet_convolution_table_exists_extensionally_unique", "dd3b6ce98b1cda129a5105bc176ffbb4e7ca7d9549ea61a8ddcfc53a4a1ced13"), ("dirichlet_convolution_table_commutative", "bcbe8d62a9c065aa28bd6caf8450e86381156e555ae1b4bcc6067a08aa6bbb40"), ("dirichlet_convolution_padded_prefix_iff", "81ea53acd86ba6b094a55b9de9d69ee97c444f5a9f5eedfa3e5e6c9afcb9002e")),
    ),
    CompletedLowerFamily(
        slug="dirichlet-fubini",
        generation=113,
        artifact="research/arithmetic-library/artifacts/dirichlet-fubini-proof-bundle-v1.json",
        artifact_bytes=4455766,
        artifact_sha256="05cb102ae5fb423e325223589eb17b8f1dd0aa8d3cb8419425142f9be087d9f3",
        count=32,
        specs_sha256="f00c81c55fe725c7595315fbec8345305bebb3e20f532e6c844c2156fa2fc6cf",
        names_sha256="79cc448d034309a22b71a3213096c0546f296f0f2a3cf76076d2acc666ef3301",
        edge_count=117,
        command_count=1962,
        rfc="research/arithmetic-library/dirichlet-fubini-associativity-rfc-v1.md",
        owned_names=("dirichlet_grid_entry_omitted", "dirichlet_grid_entry_from_factorization", "dirichlet_grid_entry_omitted_value", "dirichlet_grid_entry_factor_product", "dirichlet_grid_entry_functional", "dirichlet_grid_entry_exists", "dirichlet_grid_entry_transpose", "dirichlet_grid_flat_entry_exists", "dirichlet_grid_flat_entry_coordinates", "dirichlet_grid_flat_prefix_zero", "dirichlet_grid_flat_prefix_append", "dirichlet_grid_flat_prefix_exists", "dirichlet_grid_from_flat_prefix", "dirichlet_grid_table_exists", "dirichlet_grid_table_lookup", "dirichlet_grid_middle_factor_equation", "dirichlet_grid_entry_from_convolution_entry", "dirichlet_grid_entry_convolution_product", "dirichlet_grid_nondivisor_row_value_zero", "dirichlet_factor_row_scalar", "dirichlet_grid_row_slice", "dirichlet_grid_column_slice", "dirichlet_grid_fubini_exists", "dirichlet_factor_row_zero_sum", "dirichlet_factor_row_sum_product", "dirichlet_factor_row_nested_entry", "dirichlet_grid_row_sums_convolution_prefix", "dirichlet_grid_column_sums_convolution_prefix", "dirichlet_convolution_fubini_interchange", "dirichlet_convolution_associative", "dirichlet_convolution_tables_associative", "dirichlet_convolution_associative_tables_exists"),
        principal_roots=("dirichlet_convolution_fubini_interchange", "dirichlet_convolution_associative", "dirichlet_convolution_associative_tables_exists"),
        theorem_count=346,
        root_names=("dirichlet_convolution_associative_tables_exists",),
        node_count=347,
        dependency_edges=970,
        bundle_edges=971,
        body_nodes=25115,
        ordered_cone_names_sha256="38abb3a0095390b8906377dbfa640c859504000069268b05330bd0908696abe0",
        complete_non_alpha_specs_sha256="3f386202d5d14d9089324518122e8e40d4f9dfd53738020da649d97a0b1261fd",
        modules=("dirichlet_fubini_candidate", "dirichlet_associativity_candidate"),
        principal_pins=(("dirichlet_convolution_fubini_interchange", "52ec70863e39714463cce993fd232ffe99a1a5e0c5a97f0daecfe5b41ed8e3bd"), ("dirichlet_convolution_associative", "7963b56c370b9ff42ae43dc3e12d13dd36b6bd1dd356b62269a062a6a90d6738"), ("dirichlet_convolution_associative_tables_exists", "f0e95e4639f59cc7b592d82384c2cf72b63e594814599db6b7bf24339b35adc1")),
    ),
    CompletedLowerFamily(
        slug="dirichlet-units",
        generation=113,
        artifact="research/arithmetic-library/artifacts/dirichlet-units-proof-bundle-v1.json",
        artifact_bytes=2158014,
        artifact_sha256="232ddd461eb83d97c1a6255a872be7e970b635ce1d4e958c8bed7706419687b7",
        count=25,
        specs_sha256="954a654694207db14acb799d843520fb12b3ff2233153b07cadb7bb5c7940911",
        names_sha256="028ca36f90f03f3fd62bc9c92abadeae7a83386b0bd6b44abaefba0bb78358cf",
        edge_count=82,
        command_count=1109,
        rfc="research/arithmetic-library/dirichlet-units-rfc-v1.md",
        owned_names=("dirichlet_constant_one_table_value", "dirichlet_kronecker_delta_table_one_value", "dirichlet_kronecker_delta_table_other_value", "dirichlet_kronecker_delta_value_exists", "dirichlet_constant_one_table_append", "dirichlet_kronecker_delta_table_append", "dirichlet_constant_one_table_exists", "dirichlet_kronecker_delta_table_exists", "dirichlet_constant_one_table_reencoding", "dirichlet_constant_one_table_positive_unique", "dirichlet_kronecker_delta_table_reencoding", "dirichlet_kronecker_delta_table_positive_unique", "dirichlet_delta_right_entry_before_input", "dirichlet_delta_right_last_entry", "dirichlet_delta_right_sum_value", "dirichlet_delta_right_sum", "dirichlet_delta_right_table", "dirichlet_delta_left_table", "dirichlet_delta_unit_exists", "dirichlet_constant_one_entry_to_divisor_mask", "dirichlet_constant_one_entry_from_divisor_mask", "dirichlet_constant_one_prefix_to_divisor_mask", "dirichlet_constant_one_prefix_from_divisor_mask", "dirichlet_constant_one_sum_iff", "dirichlet_constant_one_realizes_divisor_sum"),
        principal_roots=("dirichlet_delta_unit_exists", "dirichlet_constant_one_sum_iff", "dirichlet_constant_one_realizes_divisor_sum"),
        theorem_count=281,
        root_names=("dirichlet_constant_one_table_reencoding", "dirichlet_constant_one_table_positive_unique", "dirichlet_kronecker_delta_table_reencoding", "dirichlet_kronecker_delta_table_positive_unique", "dirichlet_delta_unit_exists", "dirichlet_constant_one_realizes_divisor_sum"),
        node_count=282,
        dependency_edges=754,
        bundle_edges=760,
        body_nodes=18734,
        ordered_cone_names_sha256="d0a7c1c07b96e553f9146faf1b356bec2707d1661d5842e7a1aac0ee0c20a03e",
        complete_non_alpha_specs_sha256="941e5868847308abdf83c321ddcfbd7375eb225234872d5688026e229d564f86",
        modules=("dirichlet_units_candidate",),
        principal_pins=(("dirichlet_delta_unit_exists", "6924256ebdc7a4a8b46c532d5808e5794dea1430b6d1892c764a826191b4d710"), ("dirichlet_constant_one_sum_iff", "f502d0a59a4eb50a35be7b76d39904729a96e3d6d5c91d4e019a6aad9639908f"), ("dirichlet_constant_one_realizes_divisor_sum", "5aafb1de83c084f4d86aef3f3649ebc962a43b64c55c7356c45500c8db072d09")),
    ),
    CompletedLowerFamily(
        slug="mobius-inversion",
        generation=113,
        artifact="research/arithmetic-library/artifacts/mobius-inversion-proof-bundle-v1.json",
        artifact_bytes=6488786,
        artifact_sha256="22e7e61d5d4567df695d67830b465664fbe5a070f0367196e5cfd542ccba5b75",
        count=8,
        specs_sha256="4c40808fd2d52ae3feee2f9ab24039f2ae66aa584327c11f8bb2251cab77ef29",
        names_sha256="8c3f2f2c6a84ded9f245f11eb66b35a2202fabfa00e790cee4793ceef14c7703",
        edge_count=28,
        command_count=458,
        rfc="research/arithmetic-library/mobius-inversion-rfc-v1.md",
        owned_names=("arithmetic_divisor_transform_convolution", "arithmetic_divisor_convolution_transform", "mobius_constant_one_convolution_delta", "mobius_dirichlet_inversion_value", "mobius_inversion_for_actual_mobius_table", "mobius_inversion_arithmetic_tables", "mobius_inversion_reconstructs_divisor_transform", "mobius_inversion_iff"),
        principal_roots=("mobius_inversion_for_actual_mobius_table", "mobius_inversion_arithmetic_tables", "mobius_inversion_iff"),
        theorem_count=530,
        root_names=("arithmetic_divisor_convolution_transform", "mobius_inversion_arithmetic_tables", "mobius_inversion_iff"),
        node_count=531,
        dependency_edges=1576,
        bundle_edges=1579,
        body_nodes=40028,
        ordered_cone_names_sha256="4448254ef0f8b1cda603888a7631c0288677134b52ee209abf3308d944093209",
        complete_non_alpha_specs_sha256="1a0954abadc5e5ab952c185043925d836fb1e7f34c7cb926feffbc925b516a74",
        modules=("mobius_inversion_candidate",),
        principal_pins=(("mobius_inversion_for_actual_mobius_table", "c69a34ea1a32d3d1188c00a95754507739ed77b953a355e2ffccf0ad69e21dab"), ("mobius_inversion_arithmetic_tables", "a0cacd2561b809b9cd7e9909fd37cbbcd7a60f086560bf1bd5a2fecad5c978b9"), ("mobius_inversion_iff", "c98dbac33cefe8835eb9c023fd942e6fcb998e7bb8ca0607989b462724a8cad1")),
    ),
    CompletedLowerFamily(
        slug="dirichlet-signed-units",
        generation=40,
        artifact="research/arithmetic-library/artifacts/dirichlet-signed-units-proof-bundle-v1.json",
        artifact_bytes=214864,
        artifact_sha256="5045f1feb2f21a79ecb3cb03f95aaefeb8f01e616a4aa8640cbada3da62ae47b",
        count=9,
        specs_sha256="503e22e4a75aae8b39054144d2d3371f4c8c8f27ac584b18a1383d0e7c9660b7",
        names_sha256="5fa7ad76083b6bd935f66698b4418e6ce85720b134ce19b40696ab87433a116c",
        edge_count=36,
        command_count=401,
        rfc="research/arithmetic-library/dirichlet-signed-unit-rfc-v1.md",
        owned_names=("dirichlet_signed_unit_self_product", "dirichlet_signed_unit_product_classification", "dirichlet_signed_unit_inverse_iff", "dirichlet_signed_add_cancel_left", "dirichlet_signed_add_solve", "dirichlet_signed_unit_multiply_involution", "dirichlet_signed_unit_multiply_cancel_right", "dirichlet_signed_unit_affine_solve", "dirichlet_signed_unit_affine_unique"),
        principal_roots=("dirichlet_signed_unit_product_classification", "dirichlet_signed_unit_affine_solve", "dirichlet_signed_unit_affine_unique"),
        theorem_count=70,
        root_names=("dirichlet_signed_unit_inverse_iff", "dirichlet_signed_unit_affine_solve", "dirichlet_signed_unit_affine_unique"),
        node_count=71,
        dependency_edges=143,
        bundle_edges=146,
        body_nodes=4704,
        ordered_cone_names_sha256="4f26225d19f3f5fb27274fdf5c2f344efe7846355def2512d84242f10efb765f",
        complete_non_alpha_specs_sha256="503e22e4a75aae8b39054144d2d3371f4c8c8f27ac584b18a1383d0e7c9660b7",
        modules=("dirichlet_signed_unit_candidate",),
        principal_pins=(("dirichlet_signed_unit_product_classification", "4c6820280f2a7c6e35eb66968d2f4819ea3276baa1af24e495ec1626e963db08"), ("dirichlet_signed_unit_affine_solve", "3c8f3184a683b282d0ef7f8d9f3671f71a9b9509599ff78b4ff47623c65660e4"), ("dirichlet_signed_unit_affine_unique", "68b300d496090f0911613338c333747776a606c71fd28d4c82849bfca1c32d11")),
    ),
    CompletedLowerFamily(
        slug="dirichlet-triangular",
        generation=40,
        artifact="research/arithmetic-library/artifacts/dirichlet-triangular-proof-bundle-v1.json",
        artifact_bytes=1488366,
        artifact_sha256="d2d1b032400b46679658f6b196272df3e0869378a651e711e1b7985778e121e1",
        count=10,
        specs_sha256="a91a79108e1a636bfdd78a67e3426d33edb2e493be1d43f379aef367db743733",
        names_sha256="a94e7a4b3092b11afbfe54f8aa358f6065bcd34e1164c4f1094d52976f7cb010",
        edge_count=43,
        command_count=547,
        rfc="research/arithmetic-library/dirichlet-triangular-rfc-v1.md",
        owned_names=("dirichlet_convolution_entry_first_input_transport", "dirichlet_convolution_prefix_first_input_transport", "dirichlet_convolution_first_input_append_preserves", "dirichlet_convolution_table_first_input_append_preserves", "dirichlet_convolution_last_entry_iff", "dirichlet_convolution_strict_prefix_exists", "dirichlet_convolution_prefix_last_step", "dirichlet_convolution_first_input_append_step", "dirichlet_convolution_zero_prefix_sum", "dirichlet_convolution_at_one_iff"),
        principal_roots=("dirichlet_convolution_first_input_append_step", "dirichlet_convolution_at_one_iff", "dirichlet_convolution_strict_prefix_exists"),
        theorem_count=218,
        root_names=("dirichlet_convolution_table_first_input_append_preserves", "dirichlet_convolution_strict_prefix_exists", "dirichlet_convolution_first_input_append_step", "dirichlet_convolution_at_one_iff"),
        node_count=219,
        dependency_edges=537,
        bundle_edges=541,
        body_nodes=12776,
        ordered_cone_names_sha256="602b92865ed358b7fda398341ee58d46bd57acac9617017ea558e43325eacc73",
        complete_non_alpha_specs_sha256="e87a4474c131d8cc80559b8ccaeffe62177d7e979f9b663d94fb64455d2c5a21",
        modules=("dirichlet_triangular_candidate",),
        principal_pins=(("dirichlet_convolution_first_input_append_step", "0acd77c052775df9717c6c09715c733ab207c9fa18380b5e279222221a5f1404"), ("dirichlet_convolution_at_one_iff", "6f1888f04b4d2ac46a57cca07719bed191aa2c1e3fc6092ef671965cc8d6b956"), ("dirichlet_convolution_strict_prefix_exists", "745ac62f2fbed061d5ba9f77972361c063ec4020ed9e52144bd2a1b8a38b96d1")),
    ),
    CompletedLowerFamily(
        slug="dirichlet-inverses",
        generation=40,
        artifact="research/arithmetic-library/artifacts/dirichlet-inverses-proof-bundle-v1.json",
        artifact_bytes=7257507,
        artifact_sha256="420f08dcb5c67a260a28f391bdaa5b1f75464c73dc174fbe5cdcd4d08336c826",
        count=21,
        specs_sha256="6ccb0ee24d871bffbdedb3100445411ec03cd1d515586f5b63fa9d4780bfdf20",
        names_sha256="b320bb723eb16cb0784d550a4c28e0b41f154b466fecd7dddb1bd2d8ec8ccaea",
        edge_count=53,
        command_count=764,
        rfc="research/arithmetic-library/dirichlet-inverse-rfc-v1.md",
        owned_names=("dirichlet_unit_at_one_witness", "dirichlet_unit_at_one_from_value", "dirichlet_kronecker_delta_table_restrict", "dirichlet_inverse_from_right_delta", "dirichlet_inverse_symmetric", "dirichlet_inverse_actual_tables", "dirichlet_inverse_zero", "dirichlet_unit_equation_append", "dirichlet_unit_equation_construct", "dirichlet_inverse_from_unit", "dirichlet_inverse_from_unit_at_one", "dirichlet_inverse_zero_construct", "dirichlet_inverse_construct", "dirichlet_inverse_requires_unit_at_one", "dirichlet_inverse_positive_unique", "dirichlet_inverse_restrict", "dirichlet_inverse_prefix_compatible", "dirichlet_inverse_involution", "dirichlet_inverse_criterion", "dirichlet_inverse_positive_criterion", "dirichlet_inverse_exists_positive_unique"),
        principal_roots=("dirichlet_unit_equation_construct", "dirichlet_inverse_criterion", "dirichlet_inverse_exists_positive_unique"),
        theorem_count=400,
        root_names=("dirichlet_inverse_actual_tables", "dirichlet_inverse_prefix_compatible", "dirichlet_inverse_involution", "dirichlet_inverse_criterion", "dirichlet_inverse_positive_criterion", "dirichlet_inverse_exists_positive_unique"),
        node_count=401,
        dependency_edges=1144,
        bundle_edges=1150,
        body_nodes=29441,
        ordered_cone_names_sha256="7e4ac5be586a66bb1aa9fed7cec1c48f93b60694b3c6c396ce28596e80f4a9a5",
        complete_non_alpha_specs_sha256="60fed3b8916e0f48983be7ac2d28fa6df213ae916f7eede62bb016195aa903e6",
        modules=("dirichlet_inverse_candidate",),
        principal_pins=(("dirichlet_unit_equation_construct", "cbb0fc99f0f2eb3e77871b21e4a8d5cfe01d22c86b737e77b516f4c060f8644e"), ("dirichlet_inverse_criterion", "8c777567eae9fae4a3b6f0e0df4e4d80205c694f5b15f93f1808376e1b7d05fc"), ("dirichlet_inverse_exists_positive_unique", "eb7703bdacfaca3d2d4a6c0cf5d2a43326be82107047a7609ce053da0fedd164")),
    ),
)
FAMILIES = COMPLETED_LOWER_FAMILIES
FAMILY_BY_SLUG = MappingProxyType({family.slug: family for family in FAMILIES})
FAMILY_BY_NAME = MappingProxyType({
    name: family for family in FAMILIES for name in family.owned_names
})
FACTORY_BY_MODULE = MappingProxyType({owner.module: owner for owner in FACTORIES})
FRONTIER_NEW_NAMES = tuple(name for family in FAMILIES for name in family.owned_names)
_FACTORY_FIELDS = ("campaign", "module", "factory", "rfc", "source_bytes", "source_sha256", "count", "specs_sha256")
_FAMILY_FIELDS = ("slug", "generation", "artifact", "artifact_bytes", "artifact_sha256", "count", "specs_sha256", "names_sha256", "edge_count", "command_count", "rfc", "owned_names", "principal_roots", "theorem_count", "root_names", "node_count", "dependency_edges", "bundle_edges", "body_nodes", "ordered_cone_names_sha256", "complete_non_alpha_specs_sha256", "modules", "principal_pins")


def _metadata_digest() -> str:
    payload = (
        tuple(tuple(getattr(owner, field) for field in _FACTORY_FIELDS) for owner in FACTORIES),
        tuple(tuple(getattr(family, field) for field in _FAMILY_FIELDS) for family in FAMILIES),
    )
    return sha256(json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()


def validate_completed_lower_metadata() -> None:
    """Metadata-only eligibility; no source, artifact, catalogue or kernel calls."""
    try:
        if (
            type(FACTORIES) is not tuple or type(FAMILIES) is not tuple
            or FAMILIES is not COMPLETED_LOWER_FAMILIES
            or len(FACTORIES) != EXPECTED_COMPLETED_LOWER_FACTORY_COUNT
            or len(FAMILIES) != EXPECTED_COMPLETED_LOWER_FAMILY_COUNT
            or any(type(owner) is not CompletedLowerFactory for owner in FACTORIES)
            or any(type(family) is not CompletedLowerFamily for family in FAMILIES)
            or _metadata_digest() != EXPECTED_COMPLETED_LOWER_METADATA_SHA256
            or len(FAMILY_BY_SLUG) != len(FAMILIES)
            or len(FACTORY_BY_MODULE) != len(FACTORIES)
            or len(FAMILY_BY_NAME) != EXPECTED_COMPLETED_LOWER_COUNT
            or tuple(FAMILY_BY_NAME) != FRONTIER_NEW_NAMES
            or tuple(FAMILY_BY_SLUG.values()) != FAMILIES
            or tuple(FACTORY_BY_MODULE.values()) != FACTORIES
            or any(FAMILY_BY_NAME[name] is not family
                   for family in FAMILIES for name in family.owned_names)
            or sum(family.count for family in FAMILIES) != EXPECTED_COMPLETED_LOWER_COUNT
            or sum(family.edge_count for family in FAMILIES) != EXPECTED_COMPLETED_LOWER_EDGE_COUNT
            or sum(family.command_count for family in FAMILIES) != EXPECTED_COMPLETED_LOWER_COMMAND_COUNT
            or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
            != EXPECTED_COMPLETED_LOWER_NAMES_SHA256
        ):
            raise CompletedLowerClosureError("the completed-lower metadata seal changed")
        for owner in FACTORIES:
            if (
                re.fullmatch(r"[a-z][a-z0-9_]*_candidate", owner.module) is None
                or owner.factory != f"make_{owner.module}_theorems"
                or not 0 < owner.source_bytes <= MAX_SOURCE_BYTES
                or owner.count <= 0
                or "/" in owner.rfc or "\\" in owner.rfc or ".." in owner.rfc
                or not owner.rfc.endswith("-rfc-v1.md")
            ):
                raise CompletedLowerClosureError("invalid completed-lower factory metadata")
        for family in FAMILIES:
            if (
                not 0 < family.artifact_bytes <= DEFAULT_BUNDLE_LIMITS.max_payload_bytes
                or not 0 < family.node_count <= DEFAULT_BUNDLE_LIMITS.max_nodes
                or family.node_count != family.theorem_count + 1
                or family.bundle_edges != family.dependency_edges + len(family.root_names)
                or family.bundle_edges > DEFAULT_BUNDLE_LIMITS.max_edges
                or not 0 < family.body_nodes <= DEFAULT_BUNDLE_LIMITS.max_total_body_nodes
                or family.count != len(family.owned_names)
                or not set(family.principal_roots) <= set(family.owned_names)
                or tuple(name for name, _ in family.principal_pins) != family.principal_roots
                or not family.artifact.startswith("research/arithmetic-library/artifacts/")
                or Path(family.artifact).is_absolute() or ".." in Path(family.artifact).parts
                or tuple(owner.module for owner in FACTORIES if owner.campaign == family.slug)
                != family.modules
            ):
                raise CompletedLowerClosureError("invalid completed-lower family metadata")
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, CompletedLowerClosureError):
            raise
        raise CompletedLowerClosureError("the completed-lower metadata is malformed") from error


def completed_lower_family(slug: str) -> CompletedLowerFamily:
    validate_completed_lower_metadata()
    if type(slug) is not str or slug not in FAMILY_BY_SLUG:
        raise CompletedLowerClosureError(f"unknown completed-lower family {slug!r}")
    return FAMILY_BY_SLUG[slug]


def _read_pinned(path: Path, size: int, digest: str, *, maximum: int) -> bytes:
    """Bound before allocation/parse; a successful hash is provenance only."""
    if (type(size) is not int or not 0 < size <= maximum
            or type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
        raise CompletedLowerClosureError("invalid bounded source pin")
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise CompletedLowerClosureError(f"sealed source size/type changed: {path.name}")
        with path.open("rb") as source:
            payload = source.read(size + 1)
    except OSError as error:
        raise CompletedLowerClosureError(f"sealed source unavailable: {path.name}") from error
    if len(payload) != size or sha256(payload).hexdigest() != digest:
        raise CompletedLowerClosureError(f"sealed source bytes changed: {path.name}")
    return payload


def validate_completed_lower_source_bytes() -> tuple[CompletedLowerFactory, ...]:
    """Authenticate every new mathematical source without opening proof artifacts."""
    validate_completed_lower_metadata()
    for owner in FACTORIES:
        _read_pinned(Path(__file__).with_name(owner.module + ".py"),
                     owner.source_bytes, owner.source_sha256, maximum=MAX_SOURCE_BYTES)
    return FACTORIES


def read_completed_lower_bundle_bytes(slug: str, source: str | Path) -> bytes:
    """Read exactly one bounded frozen artifact; no acceptance claim."""
    family = completed_lower_family(slug)
    if not isinstance(source, (str, Path)):
        raise CompletedLowerClosureError("a completed-lower proof source must be a filesystem path")
    return _read_pinned(Path(source), family.artifact_bytes, family.artifact_sha256,
                        maximum=DEFAULT_BUNDLE_LIMITS.max_payload_bytes)


@lru_cache(maxsize=1)
def _load_completed_lower_specs() -> tuple[TheoremSpec, ...]:
    validate_completed_lower_source_bytes()
    rows: list[TheoremSpec] = []
    for owner in FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise CompletedLowerClosureError(f"unavailable frozen factory {owner.module}") from error
        if (
            len(candidates) != owner.count
            or any(type(row) is not TheoremSpec for row in candidates)
            or _specs_digest(candidates) != owner.specs_sha256
        ):
            raise CompletedLowerClosureError(f"exact frozen specifications changed: {owner.module}")
        rows.extend(candidates)
    result = tuple(rows)
    if (len(result) != EXPECTED_COMPLETED_LOWER_COUNT
            or tuple(row.name for row in result) != FRONTIER_NEW_NAMES
            or _specs_digest(result) != EXPECTED_COMPLETED_LOWER_SPECS_SHA256):
        raise CompletedLowerClosureError("the full completed-lower specification inventory changed")
    offset = 0
    for family in FAMILIES:
        own = result[offset:offset + family.count]
        offset += family.count
        if (
            _specs_digest(own) != family.specs_sha256
            or sum(len(row.dependencies) for row in own) != family.edge_count
            or sum(len(row.script) for row in own) != family.command_count
            or sha256("\n".join(row.name for row in own).encode()).hexdigest() != family.names_sha256
        ):
            raise CompletedLowerClosureError(f"exact family specifications changed: {family.slug}")
        by_name = {row.name: row for row in own}
        for name, digest in family.principal_pins:
            if sha256(by_name[name].statement.encode()).hexdigest() != digest:
                raise CompletedLowerClosureError(f"an exact principal statement changed: {name}")
    return result


def completed_lower_specs() -> tuple[TheoremSpec, ...]:
    """Reviewed exact syntax only; deliberately artifact-free."""
    validate_completed_lower_source_bytes()
    return _load_completed_lower_specs()


def clear_completed_lower_metadata_cache() -> None:
    _load_completed_lower_specs.cache_clear()


def _parent_specs(parent_specs: tuple[TheoremSpec, ...] | None) -> tuple[TheoremSpec, ...]:
    if parent_specs is None:
        # Native and browser installations both use installed theorem syntax.
        # No authoring registry, source checkout or catalogue is consulted.
        from . import editions_v30
        parent_specs = editions_v30.ALPHA_CHECKED_SPECS
    if (type(parent_specs) is not tuple
            or len(parent_specs) != PARENT_ALPHA_V30_COUNT
            or any(type(row) is not TheoremSpec for row in parent_specs)
            or _specs_digest(parent_specs) != PARENT_ALPHA_V30_SPECS_SHA256):
        raise CompletedLowerClosureError("the exact immutable Alpha-v30 parent syntax changed")
    return parent_specs


def completed_lower_plan(
    slug: str, *, parent_specs: tuple[TheoremSpec, ...] | None = None,
) -> CompletedLowerPlan:
    """Exact, complete topological ownership plan; no proof file is loaded."""
    family = completed_lower_family(slug)
    parent = _parent_specs(parent_specs)
    frontier = completed_lower_specs()
    inventory = (*parent, *frontier)
    table = {row.name: row for row in inventory}
    if len(table) != len(inventory):
        raise CompletedLowerClosureError("an additive theorem overwrites an existing name")
    available: set[str] = set()
    for row in inventory:
        if (type(row.dependencies) is not tuple
                or len(set(row.dependencies)) != len(row.dependencies)
                or not set(row.dependencies) <= available):
            raise CompletedLowerClosureError(f"unknown, duplicate or forward premise: {row.name}")
        available.add(row.name)
    included: set[str] = set()
    pending = list(family.owned_names)
    while pending:
        name = pending.pop()
        if name not in included:
            included.add(name)
            pending.extend(table[name].dependencies)
    selected = tuple(row for row in inventory if row.name in included)
    non_alpha = tuple(row for row in frontier if row.name in included)
    used = {name for row in non_alpha for name in row.dependencies}
    roots = tuple(row.name for row in non_alpha if row.name not in used)
    ordered_digest = sha256("\n".join(row.name for row in selected).encode()).hexdigest()
    frontier_digest = _specs_digest(non_alpha)
    edges = sum(len(row.dependencies) for row in selected)
    if (
        len(selected) != family.theorem_count
        or roots != family.root_names or not set(roots) <= set(family.owned_names)
        or ordered_digest != family.ordered_cone_names_sha256
        or frontier_digest != family.complete_non_alpha_specs_sha256
        or edges != family.dependency_edges
    ):
        raise CompletedLowerClosureError(f"the exact complete proof cone changed: {slug}")
    indices = {row.name: index for index, row in enumerate(inventory)}
    owned = frozenset(family.owned_names)
    rows = tuple(CompletedLowerRow(
        node_id=index, inventory_index=indices[row.name], name=row.name,
        statement_sha256=sha256(row.statement.encode()).hexdigest(),
        dependencies=row.dependencies,
        campaign=FAMILY_BY_NAME[row.name].slug if row.name in FAMILY_BY_NAME else None,
        is_owned=row.name in owned,
    ) for index, row in enumerate(selected))
    return CompletedLowerPlan(
        family, rows, selected, roots, tuple(row.name for row in non_alpha),
        family.owned_names, edges, ordered_digest, frontier_digest,
    )


def check_completed_lower_proof_bundle(
    slug: str, bundle: ProofBundle, target: Formula, *,
    parent_specs: tuple[TheoremSpec, ...] | None = None,
) -> CheckedProofBundle:
    """Check exact targets/ordered premises/packaging, then EVERY original HA body."""
    plan = completed_lower_plan(slug, parent_specs=parent_specs)
    family = plan.family
    positions = plan.positions
    if (type(bundle) is not ProofBundle or type(bundle.nodes) is not tuple
            or len(bundle.nodes) != family.node_count
            or type(bundle.root) is not int or bundle.root != len(plan.rows)):
        raise CompletedLowerClosureError("the complete artifact inventory or root changed")
    for row, spec, node in zip(plan.rows, plan.specs, bundle.nodes[:-1], strict=True):
        if (type(node) is not BundleNode or type(node.node_id) is not int
                or node.node_id != row.node_id
                or node.target != _closed_formula(spec.statement)
                or type(node.dependencies) is not tuple
                or any(type(value) is not int for value in node.dependencies)
                or node.dependencies != tuple(positions[name] for name in row.dependencies)):
            raise CompletedLowerClosureError(f"an exact target or ordered premise changed: {row.name}")
    by_name = {row.name: row for row in plan.specs}
    expected_target, expected_body = _packaging_root(tuple(
        _closed_formula(by_name[name].statement) for name in plan.root_names
    ))
    final = bundle.nodes[-1]
    if (type(final) is not BundleNode or type(final.node_id) is not int
            or final.node_id != len(plan.rows) or final.target != expected_target
            or final.body != expected_body or type(final.dependencies) is not tuple
            or any(type(value) is not int for value in final.dependencies)
            or final.dependencies != tuple(positions[name] for name in plan.root_names)
            or target != expected_target):
        raise CompletedLowerClosureError("the exact maximal-theorem packaging root changed")
    receipt = check_proof_bundle(bundle, target)
    if (type(receipt) is not CheckedProofBundle or receipt.target != target
            or receipt.root != bundle.root or receipt.node_count != family.node_count
            or receipt.kernel_calls != family.node_count
            or receipt.topological_order != tuple(range(family.node_count))
            or receipt.dependency_edges != family.bundle_edges
            or receipt.total_body_nodes != family.body_nodes):
        raise CompletedLowerClosureError("a complete original-kernel check or exact body metric changed")
    return receipt


__all__ = (
    "CompletedLowerClosureError", "CompletedLowerFactory", "CompletedLowerFamily",
    "CompletedLowerRow", "CompletedLowerPlan", "FACTORIES", "FAMILIES",
    "COMPLETED_LOWER_FAMILIES", "FAMILY_BY_SLUG", "FAMILY_BY_NAME",
    "FACTORY_BY_MODULE", "FRONTIER_NEW_NAMES", "completed_lower_family",
    "completed_lower_specs", "completed_lower_plan",
    "validate_completed_lower_metadata", "validate_completed_lower_source_bytes",
    "read_completed_lower_bundle_bytes", "check_completed_lower_proof_bundle",
    "clear_completed_lower_metadata_cache",
)
