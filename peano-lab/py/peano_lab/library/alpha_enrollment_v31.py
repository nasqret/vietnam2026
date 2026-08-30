"""Artifact-free exact enrollment of completed constructive lower campaigns.

The old research checkpoints remain immutable. This additive inventory is
eligible for checked Alpha use only through the new complete-body provider;
neither a saved research receipt nor a metadata digest is proof authority.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping

from . import editions_v30 as v30
from .campaign_completed_lower_closure import (
    FACTORIES, FAMILIES, FRONTIER_NEW_NAMES,
    EXPECTED_COMPLETED_LOWER_METADATA_SHA256,
    PARENT_ALPHA_V30_COUNT, PARENT_ALPHA_V30_SPECS_SHA256,
    PARENT_ALPHA_V30_ENROLLMENT_SHA256, PARENT_ALPHA_V30_IDENTITY_SHA256,
    completed_lower_specs, validate_completed_lower_metadata, _specs_digest,
)
from .theorems import TheoremSpec, _closed_formula


class AlphaV31EnrollmentError(ValueError):
    """The frozen parent, reviewed factory or additive dependency DAG changed."""


class FrontierV31Campaign(str, Enum):
    EULER_UNITS = "euler-units"
    PRIME_FIELDS = "prime-fields"
    MOBIUS_VALUES = "mobius-values"
    SIGNED_SUMS = "signed-sums"
    DIVISOR_SUMS = "divisor-sums"
    SIGNED_WEIGHTED_SUMS = "signed-weighted-sums"
    PRIME_FIELD_POLYNOMIALS = "prime-field-polynomials"
    DIVISOR_INVOLUTIONS = "divisor-involutions"
    MOBIUS_DIVISOR_CANCELLATION = "mobius-divisor-cancellation"
    RECTANGULAR_SUMS = "rectangular-sums"
    POLYNOMIAL_PRODUCTS = "polynomial-products"
    FINITE_SUPPORT = "finite-support"
    DIRICHLET_CONVOLUTION = "dirichlet-convolution"
    DIRICHLET_FUBINI = "dirichlet-fubini"
    DIRICHLET_UNITS = "dirichlet-units"
    MOBIUS_INVERSION = "mobius-inversion"
    DIRICHLET_SIGNED_UNITS = "dirichlet-signed-units"
    DIRICHLET_TRIANGULAR = "dirichlet-triangular"
    DIRICHLET_INVERSES = "dirichlet-inverses"


@dataclass(frozen=True, slots=True)
class AlphaV31Enrollment:
    parent_entries: tuple[v30.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV31Campaign]


FRONTIER_V31_EXPECTED_COUNT = 574
FRONTIER_V31_EXPECTED_EDGE_COUNT = 1660
FRONTIER_V31_EXPECTED_COMMAND_COUNT = 26004
FRONTIER_V31_EXPECTED_NAMES_SHA256 = "594e3c4766d7bcfcfafbbf6882e12f736914c9291788f548e34af12c1c6293d7"
FRONTIER_V31_EXPECTED_SPECS_SHA256 = "9ce681cbca759fcc555f582158162e9ba9cb6dbed64b57274fca530435c8c994"
EXPECTED_FACTORY_METADATA_SHA256 = "861407257104425bea809fae333a07891ef57b98c726df42acc067a260d73a99"
EXPECTED_CAMPAIGN_COUNTS = MappingProxyType({
    FrontierV31Campaign.EULER_UNITS: 32,
    FrontierV31Campaign.PRIME_FIELDS: 87,
    FrontierV31Campaign.MOBIUS_VALUES: 21,
    FrontierV31Campaign.SIGNED_SUMS: 30,
    FrontierV31Campaign.DIVISOR_SUMS: 37,
    FrontierV31Campaign.SIGNED_WEIGHTED_SUMS: 40,
    FrontierV31Campaign.PRIME_FIELD_POLYNOMIALS: 49,
    FrontierV31Campaign.DIVISOR_INVOLUTIONS: 12,
    FrontierV31Campaign.MOBIUS_DIVISOR_CANCELLATION: 28,
    FrontierV31Campaign.RECTANGULAR_SUMS: 32,
    FrontierV31Campaign.POLYNOMIAL_PRODUCTS: 53,
    FrontierV31Campaign.FINITE_SUPPORT: 8,
    FrontierV31Campaign.DIRICHLET_CONVOLUTION: 40,
    FrontierV31Campaign.DIRICHLET_FUBINI: 32,
    FrontierV31Campaign.DIRICHLET_UNITS: 25,
    FrontierV31Campaign.MOBIUS_INVERSION: 8,
    FrontierV31Campaign.DIRICHLET_SIGNED_UNITS: 9,
    FrontierV31Campaign.DIRICHLET_TRIANGULAR: 10,
    FrontierV31Campaign.DIRICHLET_INVERSES: 21,
})
EXPECTED_FACTORY_COUNTS = MappingProxyType({
    "euler_units_residue_candidate": 12,
    "euler_units_product_candidate": 14,
    "euler_units_candidate": 6,
    "prime_field_arithmetic_candidate": 42,
    "prime_field_tables_candidate": 31,
    "prime_field_finiteness_candidate": 14,
    "mobius_value_candidate": 13,
    "mobius_prime_step_candidate": 8,
    "divisor_sum_table_candidate": 14,
    "divisor_sum_algebra_candidate": 9,
    "divisor_sum_reindex_candidate": 7,
    "arithmetic_table_extension_candidate": 7,
    "mobius_table_candidate": 8,
    "divisor_mask_candidate": 22,
    "signed_table_operations_candidate": 23,
    "signed_sum_linearity_candidate": 7,
    "signed_weighted_sum_candidate": 10,
    "prime_field_polynomial_candidate": 31,
    "prime_field_polynomial_evaluation_candidate": 18,
    "divisor_involution_candidate": 12,
    "mobius_divisor_cancellation_candidate": 28,
    "signed_rectangular_slice_candidate": 15,
    "signed_rectangular_sums_candidate": 17,
    "prime_field_polynomial_convolution_candidate": 45,
    "prime_field_polynomial_degree_candidate": 8,
    "signed_finite_support_candidate": 8,
    "dirichlet_convolution_candidate": 30,
    "dirichlet_commutativity_candidate": 10,
    "dirichlet_fubini_candidate": 29,
    "dirichlet_associativity_candidate": 3,
    "dirichlet_units_candidate": 25,
    "mobius_inversion_candidate": 8,
    "dirichlet_signed_unit_candidate": 9,
    "dirichlet_triangular_candidate": 10,
    "dirichlet_inverse_candidate": 21,
})
EXPECTED_FACTORY_SOURCE_SHA256 = MappingProxyType({
    "euler_units_residue_candidate": "dacb55219a5a5e9856d208a73e39b77156977d1de7d882044d4ed52907a7fdee",
    "euler_units_product_candidate": "dfbbc7dd69672992eb99a4eb99f64fb8273c28838aa6e1e749eb5b8a075ef8b9",
    "euler_units_candidate": "46e69f301a7215929958726a12ee151ad1972b771bcee57250a8fbbf18873458",
    "prime_field_arithmetic_candidate": "d4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90",
    "prime_field_tables_candidate": "2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400",
    "prime_field_finiteness_candidate": "a86bc0d8913ebfc1ea84c8dad691db5f90e21029c612ee87ad804657b1971b28",
    "mobius_value_candidate": "18cc5aef4d4710a09bd8f2eac063ae2ccf54049a68eaab33d6b9ce7df87af9e0",
    "mobius_prime_step_candidate": "f6fe75aa8e5c899baff761edea21dc82a3b76ea52ef165511d20f34a6d332af7",
    "divisor_sum_table_candidate": "011980a3d5857c123e97359e048bb7f5b9e35685fb9d1357d1d543c4ff9d7692",
    "divisor_sum_algebra_candidate": "38cdcf7229cb43001f658bded3434d53b54efee3b28067f634e1f39af61a6c92",
    "divisor_sum_reindex_candidate": "e652ac90350d01c0ec6e4bbb7405950db316f35ff24fba3d019e1bc0c21d1ab4",
    "arithmetic_table_extension_candidate": "d39d08f7178b526daad51aaf4a75c325f567424bb8ae74906c030f4d72e9e294",
    "mobius_table_candidate": "7631337dd93f4a65e6f74ce9a5129d6701a496aa49969764c0945f4248676fc4",
    "divisor_mask_candidate": "740efabb5cbf6e0c804e901dae423e319c52c86f605ebe2a4ad0bffb033d9543",
    "signed_table_operations_candidate": "465e623dbe3fcac0eb70ca72e890d1cc8046b3a476014dc65d187b3f30f4893f",
    "signed_sum_linearity_candidate": "8da9d92ec3e204583e7539fc2ff6ca7af5677a909a59831951e978deab9d69c0",
    "signed_weighted_sum_candidate": "2cbbb6486f0a75bbf97165018ef7539dd90c8a06317d0ed037ed95afcc72db07",
    "prime_field_polynomial_candidate": "644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72",
    "prime_field_polynomial_evaluation_candidate": "9638337f69bdc1f5491255b767dc90042244402e34ceab84902b0481c2eab802",
    "divisor_involution_candidate": "67297015bcfbeb16b9090f537a2771d5c3cbfa4000d5c83c90cd0ba16cb15be7",
    "mobius_divisor_cancellation_candidate": "9af47fd019e5899586cb02c0e124579d82c4b65d093cfc73d721f411130b457f",
    "signed_rectangular_slice_candidate": "d676600c931936ff00996209c7d744c269427eaf08611fb625e471f608861e5e",
    "signed_rectangular_sums_candidate": "0ce96c5155bb7bf47f5ae2b8151631bd981263f7d05c25f6ec8b3cd365d7a26e",
    "prime_field_polynomial_convolution_candidate": "20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24",
    "prime_field_polynomial_degree_candidate": "3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5",
    "signed_finite_support_candidate": "624040e65e0852e652ecda46d2078703e8c0d062dcb06566e24e7d86e9878191",
    "dirichlet_convolution_candidate": "cec111fbad76f106a5a3f79e2d78fc2a8d483267baa1b19738d4cbfb0c0fb342",
    "dirichlet_commutativity_candidate": "1408ca915b4c335afc679b617c4189164b6701730746d3a8aa7f2a260bf75e8d",
    "dirichlet_fubini_candidate": "f18fc61cff3d778568611abebc9698e4c7da9a7dbba37d3b361597dfc988710f",
    "dirichlet_associativity_candidate": "598b0b5658dcba34f97eec4f432de111452ad734a3171832aa2e08bb13a90692",
    "dirichlet_units_candidate": "4821a0e7a8ecac28080db207dd96abf4d02a285a85da6d1173b6a1349a82b77c",
    "mobius_inversion_candidate": "79309dd26c6f434c2e8bb76858dfada758b4a2b489065403b41c70785e1bf183",
    "dirichlet_signed_unit_candidate": "263ae0497206cee991e34e08f03df3b1922fc4918e67d4d300887aa1ba7de4df",
    "dirichlet_triangular_candidate": "5b6e585a4b2df25dee069ddec17e26cddc52c329d45ee7c5fcf307314b10f8ef",
    "dirichlet_inverse_candidate": "05347563a82486859a49539e99055504720cc823e14b310389e1d90766a85379",
})
ROOT_STATEMENT_SHA256 = MappingProxyType({
    "euler_theorem_for_units": "fcfb262cc347ec2cd7624dffba31f9ed519292b3ba5f1669682cee308cbac39d",
    "euler_coprime_totient_power": "4f3533b3d207055a1f56ca77655cf26a381735fa3999f34a0a2c7935a21497e4",
    "prime_field_of_prime_order_exists": "f0a61089155f5bb6cd5e6fa79774756a296253a412e2b131bf8f491e8099b8a7",
    "mobius_value_exists_unique": "eb41094b2ceb2273e89e8966ced4cc921decf56dd6bc6dbcb5349c2087aa1135",
    "mobius_fresh_prime_negates": "2b0116e6d32e45fe7ae5e9a8bd7c11e5f95a88021cd42786276cff6e7ec303d2",
    "divisor_signed_table_reindex_exists": "f2cc667b787e62fe9e43a8689834b3edf048e4fe71b615639db1d2062d93f9f9",
    "divisor_signed_sum_permutation_invariant": "0e94ef4db7c6f73d73ae87525d29e24722764adabcd38a908ab3a844bfec57ac",
    "mobius_table_exists": "9d90a11bd987bfe516272671293b30a0d264fe613d2632c628b5701634cf5dd3",
    "signed_divisor_sum_positive_source_extensional": "5db775338790a36cdffa83a65f52f26d244827ba90942feb09600b9f5a202672",
    "signed_divisor_sum_exists_unique": "c148a766390471cd871ca467503a9a7c380142964aff8830ca412a20f743ba6d",
    "signed_weighted_sum_exists_unique": "1ed794504914ee8304903be9fce6c08e5e310c7b0e75c244382438433c4c3f14",
    "signed_weighted_sum_scalar_linearity": "488852252ab9e41daf5e2e6e234f8a9e046042f269dd9f5fd1bd9a074c45cbeb",
    "signed_weighted_sum_add_linearity": "0515fa77e429a50f266b273b77efa2682ec7cc78c3e30948559d6a5c3363f255",
    "prime_field_polynomial_horner_exists_unique": "b4e5a2cd91b33b7366aa11d591d5da743acdb244348f438797daf1be243c3941",
    "prime_field_polynomial_normalized_horner_iff": "fbed602c60a29f5b4474d678ccd397c2ff5d50e7fb52f06480c26e1938a762e5",
    "prime_field_polynomial_reduce_and_evaluate_exists": "2f0d67795bf12542c6c9fb48cb4d63d26213e8e090bbca1a7a89257a49dd0e2c",
    "positive_divisor_quotient_exists_unique": "a02a6f2e061e89191c7e4dff86b60611ebf035717468a17707bf5537486da384",
    "positive_divisor_involution_exists": "7fff4b15206b4bc27488134518c5e8231aee964a484e515576a6426be170719d",
    "divisor_complement_prefix_involution": "24bdefde49ebf80220bf5c974be3261d250dc98472d1228f6f3484492a9f34c1",
    "mobius_divisor_sum_cancellation": "dc605f677a0cdb931e7f3e65b29569dea83f1b9db136b932913a1936dc2b3406",
    "mobius_divisor_sum_cancellation_exists": "50bcf039c53ca70483eadd8ff3f9c3baf484d1fc82f84afe21009620ff674280",
    "mobius_divisor_sum_cancellation_on_positive_values": "be20bbedecba3566c7d3611f121e3d2e4fdaffd7fdee715dcd7e60afdb4cfd56",
    "signed_rectangular_slice_exists_extensionally_unique": "d0fbe7f70725333cc208f00e860d04886fafdc5fef4a36bc6e811dd88391ddd4",
    "signed_rectangular_fubini": "74787482d51c759b2472790323be3c54494bbf97fab08de48afce458898fd14d",
    "signed_rectangular_row_major_fubini": "df286640d573e43c4ce8fc84ed9a405eb4568577f4f683001adb7ae8324ff3ec",
    "prime_field_polynomial_convolution_exists_unique": "68befd01e16fc6522f2c848ddaac2bef81ead256b41bf6b03fbff132b7693410",
    "prime_field_polynomial_convolution_outside_zero": "724cc30193c104f03c1777ace6bec5f40681be6436e7da9f165d44d10cb97501",
    "prime_field_polynomial_convolution_represented_degree_exists": "8ff4406ec7462fc8e97a47932550abde9c428392cda01a1c86fe2dfd082fc51a",
    "signed_prefix_sum_zero_tail": "ae30d900f38f2fa5e22a59fe2a38056ffb4242b1fcb8ebf364c7673606f1d46b",
    "signed_prefix_sum_last_value": "d813ceef952a622bca2fb25909b732dc7c4f9987720b050a3c5a41b590690013",
    "signed_prefix_sum_zero_padding_iff": "0a6919b464fecaa0138aef0d8ce9f24d3e2f48357a29544523c17e67b3200f4e",
    "dirichlet_convolution_table_exists_extensionally_unique": "dd3b6ce98b1cda129a5105bc176ffbb4e7ca7d9549ea61a8ddcfc53a4a1ced13",
    "dirichlet_convolution_table_commutative": "bcbe8d62a9c065aa28bd6caf8450e86381156e555ae1b4bcc6067a08aa6bbb40",
    "dirichlet_convolution_padded_prefix_iff": "81ea53acd86ba6b094a55b9de9d69ee97c444f5a9f5eedfa3e5e6c9afcb9002e",
    "dirichlet_convolution_fubini_interchange": "52ec70863e39714463cce993fd232ffe99a1a5e0c5a97f0daecfe5b41ed8e3bd",
    "dirichlet_convolution_associative": "7963b56c370b9ff42ae43dc3e12d13dd36b6bd1dd356b62269a062a6a90d6738",
    "dirichlet_convolution_associative_tables_exists": "f0e95e4639f59cc7b592d82384c2cf72b63e594814599db6b7bf24339b35adc1",
    "dirichlet_delta_unit_exists": "6924256ebdc7a4a8b46c532d5808e5794dea1430b6d1892c764a826191b4d710",
    "dirichlet_constant_one_sum_iff": "f502d0a59a4eb50a35be7b76d39904729a96e3d6d5c91d4e019a6aad9639908f",
    "dirichlet_constant_one_realizes_divisor_sum": "5aafb1de83c084f4d86aef3f3649ebc962a43b64c55c7356c45500c8db072d09",
    "mobius_inversion_for_actual_mobius_table": "c69a34ea1a32d3d1188c00a95754507739ed77b953a355e2ffccf0ad69e21dab",
    "mobius_inversion_arithmetic_tables": "a0cacd2561b809b9cd7e9909fd37cbbcd7a60f086560bf1bd5a2fecad5c978b9",
    "mobius_inversion_iff": "c98dbac33cefe8835eb9c023fd942e6fcb998e7bb8ca0607989b462724a8cad1",
    "dirichlet_signed_unit_product_classification": "4c6820280f2a7c6e35eb66968d2f4819ea3276baa1af24e495ec1626e963db08",
    "dirichlet_signed_unit_affine_solve": "3c8f3184a683b282d0ef7f8d9f3671f71a9b9509599ff78b4ff47623c65660e4",
    "dirichlet_signed_unit_affine_unique": "68b300d496090f0911613338c333747776a606c71fd28d4c82849bfca1c32d11",
    "dirichlet_convolution_first_input_append_step": "0acd77c052775df9717c6c09715c733ab207c9fa18380b5e279222221a5f1404",
    "dirichlet_convolution_at_one_iff": "6f1888f04b4d2ac46a57cca07719bed191aa2c1e3fc6092ef671965cc8d6b956",
    "dirichlet_convolution_strict_prefix_exists": "745ac62f2fbed061d5ba9f77972361c063ec4020ed9e52144bd2a1b8a38b96d1",
    "dirichlet_unit_equation_construct": "cbb0fc99f0f2eb3e77871b21e4a8d5cfe01d22c86b737e77b516f4c060f8644e",
    "dirichlet_inverse_criterion": "8c777567eae9fae4a3b6f0e0df4e4d80205c694f5b15f93f1808376e1b7d05fc",
    "dirichlet_inverse_exists_positive_unique": "eb7703bdacfaca3d2d4a6c0cf5d2a43326be82107047a7609ce053da0fedd164",
})


def _validate_parent() -> None:
    if (
        len(v30.ALPHA_ENTRIES) != PARENT_ALPHA_V30_COUNT
        or len(v30.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V30_COUNT
        or v30.ALPHA_V30_ENROLLMENT_SHA256 != PARENT_ALPHA_V30_ENROLLMENT_SHA256
        or v30.ALPHA_V30_IDENTITY_SHA256 != PARENT_ALPHA_V30_IDENTITY_SHA256
        or _specs_digest(v30.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V30_SPECS_SHA256
        or len(v30.STABLE_SPECS) != 432
    ):
        raise AlphaV31EnrollmentError("the immutable completely checked Alpha-v30 parent changed")


@lru_cache(maxsize=1)
def alpha_v31_enrollment() -> AlphaV31Enrollment:
    validate_completed_lower_metadata()
    _validate_parent()
    metadata = tuple((
        owner.campaign, owner.module, owner.factory, owner.rfc,
        owner.source_bytes, owner.source_sha256, owner.count, owner.specs_sha256,
    ) for owner in FACTORIES)
    if (
        tuple(owner.module for owner in FACTORIES) != tuple(EXPECTED_FACTORY_COUNTS)
        or sha256(json.dumps(metadata, separators=(",", ":")).encode()).hexdigest()
        != EXPECTED_FACTORY_METADATA_SHA256
        or any(owner.count != EXPECTED_FACTORY_COUNTS[owner.module]
               or owner.source_sha256 != EXPECTED_FACTORY_SOURCE_SHA256[owner.module]
               for owner in FACTORIES)
    ):
        raise AlphaV31EnrollmentError("the literal Alpha-v31 factory inventory changed")
    rows = completed_lower_specs()
    if (
        len(rows) != FRONTIER_V31_EXPECTED_COUNT
        or tuple(row.name for row in rows) != FRONTIER_NEW_NAMES
        or sha256("\n".join(row.name for row in rows).encode()).hexdigest()
        != FRONTIER_V31_EXPECTED_NAMES_SHA256
        or _specs_digest(rows) != FRONTIER_V31_EXPECTED_SPECS_SHA256
        or sum(len(row.dependencies) for row in rows) != FRONTIER_V31_EXPECTED_EDGE_COUNT
        or sum(len(row.script) for row in rows) != FRONTIER_V31_EXPECTED_COMMAND_COUNT
    ):
        raise AlphaV31EnrollmentError("the complete additive Alpha-v31 specifications changed")
    available = {entry.spec.name for entry in v30.ALPHA_ENTRIES}
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV31Campaign] = {}
    offset = 0
    for owner in FACTORIES:
        local = rows[offset:offset + owner.count]
        offset += owner.count
        campaign = FrontierV31Campaign(owner.campaign)
        for item in local:
            if (
                type(item) is not TheoremSpec or item.name in available
                or type(item.dependencies) is not tuple
                or len(set(item.dependencies)) != len(item.dependencies)
                or not set(item.dependencies) <= available
                or type(item.script) is not tuple or not item.script
                or any(type(command) is not str or not command.strip()
                       or "DNE" in command or command.startswith(("use ", "admit", "sorry"))
                       for command in item.script)
            ):
                raise AlphaV31EnrollmentError(f"invalid additive constructive theorem {item.name!r}")
            _closed_formula(item.statement)
            available.add(item.name)
            sources[item.name] = owner.source
            tests[item.name] = owner.test
            rfcs[item.name] = "research/arithmetic-library/" + owner.rfc
            campaigns[item.name] = campaign
    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV31EnrollmentError("the exact Alpha-v31 campaign ownership counts changed")
    by_name = {row.name: row for row in rows}
    for name, digest in ROOT_STATEMENT_SHA256.items():
        if name not in by_name or sha256(by_name[name].statement.encode()).hexdigest() != digest:
            raise AlphaV31EnrollmentError(f"an exact principal statement changed: {name}")
    return AlphaV31Enrollment(
        v30.ALPHA_ENTRIES, rows, MappingProxyType(sources), MappingProxyType(tests),
        MappingProxyType(rfcs), MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV31Enrollment", "AlphaV31EnrollmentError", "FrontierV31Campaign",
    "alpha_v31_enrollment", "EXPECTED_CAMPAIGN_COUNTS", "EXPECTED_FACTORY_COUNTS",
    "EXPECTED_FACTORY_METADATA_SHA256", "EXPECTED_FACTORY_SOURCE_SHA256",
    "FRONTIER_V31_EXPECTED_COUNT", "FRONTIER_V31_EXPECTED_EDGE_COUNT",
    "FRONTIER_V31_EXPECTED_COMMAND_COUNT", "FRONTIER_V31_EXPECTED_NAMES_SHA256",
    "FRONTIER_V31_EXPECTED_SPECS_SHA256", "PARENT_ALPHA_V30_COUNT",
    "PARENT_ALPHA_V30_SPECS_SHA256", "PARENT_ALPHA_V30_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V30_IDENTITY_SHA256", "ROOT_STATEMENT_SHA256",
)
