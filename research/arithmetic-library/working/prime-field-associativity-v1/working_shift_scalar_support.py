"""Exact, non-admitting syntax for the frozen shift15 + scalar10 tranche.

Only canonical inherited modules are used. No working module is installed
in sys.modules, no production alias is replaced, and no edition is imported
by source planning or proof workers. Catalogue parsing belongs exclusively
to the separate current-v33 novelty window. Digests identify inputs; actual
original HA and same-byte compiled Lean remain separate mandatory gates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import re
import stat
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING_RELATIVE = "research/arithmetic-library/working/prime-field-associativity-v1"
if HERE != ROOT / WORKING_RELATIVE or not (ROOT / "peano-lab/py/peano_lab").is_dir():
    raise RuntimeError("the shift/scalar integration belongs only in its new working directory")
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import constructive_g009_support as inherited
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.proof_bundle import encode_formula
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula

closure, FilePin = inherited.closure, inherited.FilePin
canonical, bounded_bytes, check_pin = inherited.canonical, inherited.bounded_bytes, inherited.check_pin
MAX_SOURCE_BYTES = inherited.MAX_SOURCE_BYTES
MAX_BYTES = closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes
MAX_CATALOG_BYTES = inherited.MAX_CATALOG_COMPONENT_BYTES
CPU_LIMITS, WALL_SECONDS, MAX_RSS_BYTES = (170, 175), 180, 1536 * 1024 * 1024
EXPECTED_COUNT, EXPECTED_INHERITED_COUNT = 25, 182
SPECS_SHA256 = "15d48cfcf25a997db2e18771d0c084f4465225c6137f47f53350d39a5ebb6981"
ARTIFACT_DIRECTORY = HERE / "artifacts"
OUTPUT_PREFIX = "working-shift-scalar-"
CONTROL_FILES = (
    "working_shift_scalar_support.py", "export_working_shift_scalar.py",
    "check_working_shift_scalar.py", "test_working_shift_scalar_integration.py",
    "working-shift-scalar-integration-rfc-v1.md",
)
PRINCIPAL_ROOTS = (
    "prime_field_polynomial_convolution_shift_right_nonempty",
    "prime_field_polynomial_convolution_shift_right_equivalent",
    "prime_field_polynomial_convolution_shift_right_exists",
    "prime_field_polynomial_shift_power_successor",
    "prime_field_polynomial_convolution_right_scale",
    "prime_field_polynomial_convolution_right_scale_equal",
    "prime_field_polynomial_convolution_right_scale_exists",
)
PRINCIPAL_STATEMENT_SHA256 = (
    "6f60c7f6c17e34de78a145b9a6cb532ca29ba7a0a3b13d3c7b4abc78973bbe00",
    "56aeba7667a7fc9ee6253ce009cc56e950d24249a3e1fbd4efb25f3bef7558b0",
    "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d",
    "95f29368de026c7478030396755847941e66199186ea801fb3f3e9f635f86ba7",
    "b0ed0acc0a69da43be5864e35d7b089dd83f35d3df5fa493c2716867d8e0c8f4",
    "42cae7e1cc12bbe6b7b33d8060e1c66b7b46555d983ade711fd09d5545cb5e6c",
    "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156",
)


class WorkingError(ValueError):
    """A real source, exact ownership, closure, or unchanged gate failed."""


@dataclass(frozen=True, slots=True)
class Factory:
    directory: str
    module: str
    count: int
    source_bytes: int
    source_sha256: str
    test_bytes: int
    test_sha256: str
    specs_sha256: str

    @property
    def source(self):
        return FilePin(self.directory + "/" + self.module + ".py", self.source_bytes, self.source_sha256)

    @property
    def test(self):
        return FilePin(self.directory + "/test_" + self.module + ".py", self.test_bytes, self.test_sha256)

    @property
    def factory(self):
        return "make_" + self.module + "_theorems"


FACTORIES = (
    Factory("research/arithmetic-library/working/prime-field-shift-v1",
            "prime_field_polynomial_shift_candidate", 15, 29786,
            "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b",
            32010, "0622fb92978fcf028842aa4d9822ef61213642eb852e080f7c787dcea4bb395f",
            "beac32710e2191f4dc40f6317dc376f6b3307ad8ad48a7ccbac17c8bea990081"),
    Factory("research/arithmetic-library/working/prime-field-scalar-v1",
            "prime_field_polynomial_scalar_convolution_candidate", 10, 23637,
            "e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e",
            30353, "881452ada0b5dc3be7d6cd00ee31dc08075b07f51d83595ee60f8cfb40d4c6e5",
            "a8ab3e2660a01dc79520722de6093c534e4184dcdbcb9481317df4d5b6a54a7b"),
)
_FACTORY_RECORDS = tuple(asdict(owner) for owner in FACTORIES)

# All actual canonical import inputs measured by source-only construction,
# together with the inherited literal kernel/compiler/control pins. Merely
# reading an older edition's bytes does not import or execute that edition.
RUNTIME_PINS = (
    FilePin("peano-lab/py/peano_lab/__init__.py", 257, "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a"),
    FilePin("peano-lab/py/peano_lab/engine/__init__.py", 286, "1fbd27721e00e873b4b6839508b63889e6ba8a4a51165b11e042c05270d1308b"),
    FilePin("peano-lab/py/peano_lab/engine/compact_arith.py", 49086, "8e9d6330e7594e54a7b7917d9b95c5335a3bba2b38ce16c7d6c458c5c38d8fc0"),
    FilePin("peano-lab/py/peano_lab/engine/decide.py", 17710, "07044458d92b68781d95091fabbe0fbc4a476c58f3821e0c806553e0813c2e0a"),
    FilePin("peano-lab/py/peano_lab/engine/induction.py", 6433, "4bb1db5f3b944e1f9a0ebe388ab76970aae055bf4d1171d896fbb0323172545f"),
    FilePin("peano-lab/py/peano_lab/engine/norm_num.py", 16127, "79d9ebe369348779aca6c7f12932a1204756a13d631ebd69f2612de082ab13b1"),
    FilePin("peano-lab/py/peano_lab/engine/proof_reduction.py", 23381, "deb17a5a0d5562f73248d6fbaa8db46b923c7bab07e491f37cb98e5e19a8251f"),
    FilePin("peano-lab/py/peano_lab/engine/rewrite.py", 28506, "05f0b5fe8d46910d9cc2b1604d96756aa68e42339ca90afc094d60bfce48aa5f"),
    FilePin("peano-lab/py/peano_lab/engine/ring.py", 43196, "7ba5c4b4085725677ba984afa8a50cee8061ce9ba333b644993ecff5fd5f249e"),
    FilePin("peano-lab/py/peano_lab/engine/search.py", 15634, "935d50ce4ad81e9a0a0483e8b52c61be93049ead02f8f0971ad58b6f9326e415"),
    FilePin("peano-lab/py/peano_lab/engine/state.py", 22928, "368aa1a6d8e57b48396c0f17d124c280c7ebf5cfdbe8086bc053940af5f72e68"),
    FilePin("peano-lab/py/peano_lab/engine/tacticals.py", 11282, "9285da2f6bc3ebebaa6c341b5dc94dd9282c6886b78ec8b8beebd58dc68536d6"),
    FilePin("peano-lab/py/peano_lab/engine/tactics.py", 69649, "23307a7dde5a16e72ae844ad9762a3a95e14406f6da44c412a51be20eae6e69d"),
    FilePin("peano-lab/py/peano_lab/engine/trace.py", 17735, "d9a7b2aa789fefd8d0da8d6ce6b6ae37b925f92a3e611e0809b02cd5e9173df7"),
    FilePin("peano-lab/py/peano_lab/kernel/__init__.py", 263, "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84"),
    FilePin("peano-lab/py/peano_lab/kernel/checker.py", 10021, "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe"),
    FilePin("peano-lab/py/peano_lab/kernel/formulas.py", 10950, "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645"),
    FilePin("peano-lab/py/peano_lab/kernel/proofs.py", 5015, "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2"),
    FilePin("peano-lab/py/peano_lab/kernel/subst.py", 5165, "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3"),
    FilePin("peano-lab/py/peano_lab/kernel/terms.py", 11144, "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5"),
    FilePin("peano-lab/py/peano_lab/library/__init__.py", 299, "70035fa65aafe8bed7a7b1538b0f4fdbf895ca1d5ddeef3625b9fdb9fb4e77e5"),
    FilePin("peano-lab/py/peano_lab/library/alpha_enrollment_v30.py", 11831, "ca61a5efa17c8624c29ad3388c97743947a81f648e7f1aeeef848833cd484bac"),
    FilePin("peano-lab/py/peano_lab/library/alpha_enrollment_v31.py", 19548, "7106c15b7196ca70d4bd62a4708696bd38e9b4eee07a127844c2d8398cd6e81b"),
    FilePin("peano-lab/py/peano_lab/library/binary_modular_exponentiation_candidate.py", 37701, "e30f2c6c7afced6a25449ab429bbcb04452650eb5dd02b256984e7fe4904ab13"),
    FilePin("peano-lab/py/peano_lab/library/campaign_bottom_layer_closure.py", 22539, "e4d6f74feabf16ac342c9bfb875a39d060f5b97039866ae3a0a5fea99db84477"),
    FilePin("peano-lab/py/peano_lab/library/campaign_completed_lower_closure.py", 92122, "9aec583406e6b890fdd626cb60ecf8de4271581e20e86e1aa8499a4b1701dab3"),
    FilePin("peano-lab/py/peano_lab/library/campaign_gaussian_factorization_closure.py", 38094, "68af15379776c0cb36125c1d2f24e7c87b98880a7caad24725453937b864ac3e"),
    FilePin("peano-lab/py/peano_lab/library/campaign_lower_layer_closure.py", 24500, "d7b31c8511d4439e1a2075cba718b2cba0fd7ea42a07c2ffb41d55dd7e75542c"),
    FilePin("peano-lab/py/peano_lab/library/defined_syntax.py", 37539, "86b3ee6dc17043553e730372ac0d9af884a3fb85ebe6a30813318871145fe903"),
    FilePin("peano-lab/py/peano_lab/library/editions_v30.py", 18555, "88499fde8ae5b19be5fea2d2d88d3ab56c0a27901abdbf6f005c16a0c1c1328f"),
    FilePin("peano-lab/py/peano_lab/library/editions_v31.py", 18745, "24fedcd8a492578f9a1e32bdd984693bd8e27216105000f719188a3a38200870"),
    FilePin("peano-lab/py/peano_lab/library/finite_bitcount_theorems.py", 12099, "4704e64d968b6ff19d302ef404dac38a8510aff980fd41063dde0010d6390e6c"),
    FilePin("peano-lab/py/peano_lab/library/finite_congruence_theorems.py", 12391, "d82ad67620210cd81741bc8eb287569f9bf5124714ba50da65985c7d33a8ec68"),
    FilePin("peano-lab/py/peano_lab/library/finite_division_prefix_candidate.py", 13578, "a6af47a7d918d46cdd4b83f60524d3c7afad42886ebb8e560bda5a1318f0b606"),
    FilePin("peano-lab/py/peano_lab/library/finite_factorial_theorems.py", 11579, "a51240629fb661c3d732cb30ad32d3fdc1d3da8b9d01f80023f12429dc7e3709"),
    FilePin("peano-lab/py/peano_lab/library/finite_fold_surface.py", 12423, "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30"),
    FilePin("peano-lab/py/peano_lab/library/finite_fold_theorems.py", 16292, "e69c41198d25aa0cba3bbf8415344050b28ecb8d058c1cd8d98415e0db09178c"),
    FilePin("peano-lab/py/peano_lab/library/finite_omission_candidate.py", 36329, "4633d2fa461dadc2c375be10a560e68232de94435b4d153bf562b76410558f3a"),
    FilePin("peano-lab/py/peano_lab/library/finite_permutation_theorems.py", 83518, "6265e4cf5938beadbf77182b7a5357a9435abd9948015a955539b451430420ce"),
    FilePin("peano-lab/py/peano_lab/library/finite_pointwise_mul_product_candidate.py", 13432, "d7f79aad4af594445d0d05eafc4ee8a2c38d755eb8f736af4734a2d32e6f9899"),
    FilePin("peano-lab/py/peano_lab/library/finite_pointwise_mul_recode_candidate.py", 15489, "390e453959339720836e37ea488f226db3ad0c2fabe9dc53572053801e0c9dd3"),
    FilePin("peano-lab/py/peano_lab/library/finite_product_permutation_theorems.py", 22212, "a9d799a189d8061b1ee97f163172f95396a35819cfef791543407ee0a34aea5a"),
    FilePin("peano-lab/py/peano_lab/library/finite_product_reindex_support.py", 13335, "7adf1f63c23e39ab1428061355cebb3caddd3bf51e909185ec22d83b6442fc7c"),
    FilePin("peano-lab/py/peano_lab/library/finite_range_theorems.py", 8163, "8ca4812b8059e76ec2faf4e4269d5192adee320df281b16dacfd5e7b9682833f"),
    FilePin("peano-lab/py/peano_lab/library/finite_repeat_sum_candidate.py", 6860, "7e468d7ddced0220b4c6da6c7417edfa1f1392e793770b0109808ad32d84d182"),
    FilePin("peano-lab/py/peano_lab/library/finite_sum_pointwise_mod_candidate.py", 16646, "8e6c55bc4700302d57959e3318b595d616b185b3af5329988b17b295a929de8a"),
    FilePin("peano-lab/py/peano_lab/library/finite_sum_theorems.py", 25228, "0d60b7a4fa21161def737fc6759b23e0679694052e95d97b419aa1ecb293c56e"),
    FilePin("peano-lab/py/peano_lab/library/finite_sum_transport_candidate.py", 4087, "5b875f94f987c8f7b77a8ef227d2209dfb209244a38f2b7b03c6197034578023"),
    FilePin("peano-lab/py/peano_lab/library/formula_dag.py", 20794, "3dfd0ad9ec3270cb2cd40948b62f223ba9e5f7284152c823405d8002b7a1a45f"),
    FilePin("peano-lab/py/peano_lab/library/gauss_half_range.py", 11730, "3653e994bc5862c686d21a9597e0aef19302eccdbcc3badffc260918b2a656d7"),
    FilePin("peano-lab/py/peano_lab/library/gauss_sign_bridge.py", 9847, "2ea4ae59ea1d5120d93af74d7f4c1cff624c9ad3a0aeac36d3b8dd2901412b76"),
    FilePin("peano-lab/py/peano_lab/library/gauss_signed_prefix_candidate.py", 40602, "1c55b39e8a8984b65c567582cb42cdcf8424fd595adf6bdf5162b4a575b5e901"),
    FilePin("peano-lab/py/peano_lab/library/ha_canonical_congruence_candidate.py", 6867, "7b11879d25f4d0a7f7c8b9aa4585adc24a073ca94ac0aa897b002f37e4e409c6"),
    FilePin("peano-lab/py/peano_lab/library/ha_canonical_gcd_candidate.py", 6377, "8d6b7675a520726ee945ad165b23cd75d820561a67596d40906f5c61859edc2b"),
    FilePin("peano-lab/py/peano_lab/library/ha_canonical_gcd_edges_candidate.py", 11153, "4d5f5221356a257a19843e2e3028bf2e6ef4062bf18761b1cda625986c5f8997"),
    FilePin("peano-lab/py/peano_lab/library/ha_canonical_remainder_candidate.py", 7200, "d96c02811a2c8e3155d25c62b4b2e1e0ee5a854b3bcfbdfd3b97744589d133d3"),
    FilePin("peano-lab/py/peano_lab/library/ha_generalized_crt_canonical_boundary_candidate.py", 21752, "4bc5d47961c1b3fc5bf80227d26b05a86ed8f4c6e1a775f6dbf0d63beda3a144"),
    FilePin("peano-lab/py/peano_lab/library/ha_generalized_crt_classification_candidate.py", 19079, "56c8acc5592ac98ae45827b3774a7b29435faa2a751c30d19f84383b1be31e23"),
    FilePin("peano-lab/py/peano_lab/library/ha_generalized_crt_congruence_candidate.py", 18256, "3f22b381e60a2fb78e5617b0a9ca1a0deee63ee9980dc17dfacc048ce3dbb976"),
    FilePin("peano-lab/py/peano_lab/library/ha_generalized_crt_decision_candidate.py", 7248, "a217a4b16f51a266ac42d544a8427c70b5145da8e0e17ee83892e59389a71d30"),
    FilePin("peano-lab/py/peano_lab/library/ha_generalized_crt_sufficiency_candidate.py", 25154, "56f391dfbac666dfdc30174a4e8b0f0c79185af000f26fe3b69be8cd4bfc5da8"),
    FilePin("peano-lab/py/peano_lab/library/ha_generalized_crt_total_decision_candidate.py", 3324, "cbdb7b81c7ea278744dc2e394c7d7bc72e1699bf5ab272d6e34bdf6a048d96d8"),
    FilePin("peano-lab/py/peano_lab/library/ha_generalized_crt_zero_boundary_candidate.py", 11746, "32d067f86d8e64ebfcbba44e321ca2fc3db865d0c66bacb75607df8881497fa9"),
    FilePin("peano-lab/py/peano_lab/library/ha_lcm_totality_bridge_candidate.py", 25580, "9fe014c05510362056940c36953e3c78cd1569f1592ce441070a7e9ba42e6d05"),
    FilePin("peano-lab/py/peano_lab/library/ha_modular_inverse_candidate.py", 13643, "71492661e7ee591b9c2c5e1ecb685e5b1ddea12637b717f74207c68425b08190"),
    FilePin("peano-lab/py/peano_lab/library/ha_relational_lcm_candidate.py", 17431, "ea3eb6ebb3063406acc24b0ac85bb36c4418c0826fa081eb4936eddc4265e3cd"),
    FilePin("peano-lab/py/peano_lab/library/hensel_prime_power_candidate.py", 41831, "507e76d5ad70e9244313de145036f64891f39ae40de74fcddde112deb8885bc3"),
    FilePin("peano-lab/py/peano_lab/library/layered_replay.py", 35376, "7c8b14b95ab76fe10f265a10271fd58f779fab3b7524c8f9002884b753b2badf"),
    FilePin("peano-lab/py/peano_lab/library/matrix_coded_product_candidate.py", 73949, "621d47e1a2d3ba9a55ee4779583b7ac7b0cc7192e91ded4141e6e705e9bb0fc2"),
    FilePin("peano-lab/py/peano_lab/library/matrix_cofactor_expansion_candidate.py", 77860, "536186acaec31f9f662e3aff3a5bf0769487fb8414e5d25180174e197c193fa9"),
    FilePin("peano-lab/py/peano_lab/library/matrix_determinant_minors_candidate.py", 50434, "eb5f3c55eec62b61db82a3c7a890d177f939a0792119b6d6b56c47b329aca85d"),
    FilePin("peano-lab/py/peano_lab/library/matrix_dot_product_candidate.py", 21798, "989b6eb9c547122662c3dc3585b9494e2f54919a149dc21f40ce3a82358495c2"),
    FilePin("peano-lab/py/peano_lab/library/matrix_recursive_determinant_candidate.py", 42271, "f2255bab15d10ee3906730d9dcbd06352a839381c352f6c0d6eed458a5c1d7df"),
    FilePin("peano-lab/py/peano_lab/library/parity.py", 16914, "f39325d72c0f29969b6e01cfd92451fe29f911a485a628f2baa33c0319dcf2da"),
    FilePin("peano-lab/py/peano_lab/library/polynomial_hensel_candidate.py", 43458, "55f9e8bee6bae75e6f647b7bfd5740689ed09930b93eae14d1e0307864ddccf5"),
    FilePin("peano-lab/py/peano_lab/library/polynomial_horner_candidate.py", 16967, "e2fb1f80f81a5f7b2b6915dc6981f0bfa04c4f1c5e16b62b46e102ff31d16c4f"),
    FilePin("peano-lab/py/peano_lab/library/polynomial_taylor_hensel_candidate.py", 61639, "f5c0fa2effd4450afc5421736fd7fda38bf433cca7adff1c2cf5cfa528506563"),
    FilePin("peano-lab/py/peano_lab/library/power_algebra_theorems.py", 13426, "6566c3539a18801c32d0a3ae7b6abe242bb8cf62e95184271680f0303b6fc302"),
    FilePin("peano-lab/py/peano_lab/library/power_congruence_theorems.py", 10232, "f1b34a176f9c77d60ef7dd1908ec7e6163608f684451c992dbd9fb8dacf34423"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_arithmetic_candidate.py", 39963, "d4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_candidate.py", 45723, "644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_convolution_candidate.py", 49060, "20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_convolution_triangular_candidate.py", 16677, "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_degree_candidate.py", 12579, "3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_representation_candidate.py", 42623, "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_subtraction_candidate.py", 27165, "d08562b26c683a891e58a4b10faa495867d7487054b1ee7c99f091dd1c707b2b"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_polynomial_trim_candidate.py", 26425, "1125c02fd11646efaa20963380ba1086e18551f2c89b242b8900a8043d358e4c"),
    FilePin("peano-lab/py/peano_lab/library/prime_field_tables_candidate.py", 28103, "2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400"),
    FilePin("peano-lab/py/peano_lab/library/proof_bundle.py", 26383, "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4"),
    FilePin("peano-lab/py/peano_lab/library/qr_bounded_units.py", 10872, "1ca3673054052094c32cabfca6a59f7e801ccd51b1fd9fee780d52fecaa70562"),
    FilePin("peano-lab/py/peano_lab/library/qr_prime_units.py", 19517, "ea611d606ed0b345e75e230c77ea9ec5ee5ce9a2b1d85ae400c2ac94819c11cd"),
    FilePin("peano-lab/py/peano_lab/library/qr_small_moduli.py", 15230, "fb8dbbb75817e15f4e522e6d4ce20a0b4a13f4a836872ad6b8de6ed51c0d5530"),
    FilePin("peano-lab/py/peano_lab/library/quadratic_residue_surface.py", 8724, "ab7abd5b9fcf306035de6eb849ad65f8287e84e6cc00ad909aeed7e880915246"),
    FilePin("peano-lab/py/peano_lab/library/quadratic_residue_theorems.py", 19823, "d08e6a29295be014c67ec52d8cf7b67cc4b7c99abe6dde3708c162beccc4126d"),
    FilePin("peano-lab/py/peano_lab/library/theorems.py", 536011, "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919"),
    FilePin("peano-lab/py/peano_lab/library/wilson_inverse_point_candidate.py", 15918, "690b85e26e309ea234728c6c25202406343026c2c99f08866af4fab401762737"),
    FilePin("scripts/check_constructive_bottom_layers.py", 2891, "5a2d4225cd82498ff6988d9dcb84cd18bb865e6d7318cb99752f0fe34fcad34f"),
    FilePin("scripts/check_constructive_lower_continuation.py", 19402, "0db0df31d763ae2b747fd2eb3315066fc17c3be049ff481641a149fc2665603b"),
    FilePin("scripts/constructive_bottom_layer_checkpoints.py", 14684, "edbab69b368b2944ceb38d6c7cee856c04c570ef6f7dc167f73528dd9581ab15"),
    FilePin("scripts/constructive_g009_support.py", 28875, "9fd66073e9cdcb98746c108da45b832105eb1007ea5a4a412ede01b08403bf9c"),
    FilePin("scripts/peano_catalog_shards_v32.py", 15337, "ad75eaf7b0d2ef93ec01fba456860c8421a0f23b17fba7bb508be32763c5c92a"),
    FilePin("scripts/peano_catalog_shards_v33.py", 15000, "5d9afabdc3155cc99e9e81b799d4a8d8a96681e31d0f576313d5fe7deb58c91f"),
    FilePin("scripts/peano_catalog_shards.py", 29340, "961d2698a309795e91ce8fc32564ea5113e6f36ed2798301c805e58c560942b9"),
)
_RUNTIME_RECORDS = tuple((pin.path, pin.bytes, pin.sha256) for pin in RUNTIME_PINS)
_RUNTIME_BY_PATH = {pin.path: pin for pin in RUNTIME_PINS}
PROVIDER_MODULES = (
    "prime_field_arithmetic_candidate", "prime_field_polynomial_candidate",
    "prime_field_polynomial_convolution_candidate",
    "prime_field_polynomial_representation_candidate",
    "finite_division_prefix_candidate", "finite_pointwise_mul_recode_candidate",
    "finite_repeat_sum_candidate", "finite_sum_transport_candidate",
    "binary_modular_exponentiation_candidate", "hensel_prime_power_candidate",
)

# Literal historical archives are read for preservation only, never imported.
PRESERVED_ARCHIVES = (
    ("research/arithmetic-library/working/prime-field-euclidean-v1", 43, "8c5d3190f0da93e8925205ea56fcbb3f24efd20d65ef9de3dc349f93b6d8969b"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1", 21, "9613eeafd9797dcf9bfa83d08161c16d2f4d6eb7aa20428bfc10aed2379fa62f"),
)
_ARCHIVE_IDENTITIES = PRESERVED_ARCHIVES
INITIAL_SEED = FilePin(
    "research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json",
    2449379, "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf")
SUPPLEMENTAL_SEEDS = (
    FilePin("research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json",
            745307, "55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3"),
    FilePin("research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json",
            688987, "6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a"),
)
SEED_PINS = (INITIAL_SEED, *SUPPLEMENTAL_SEEDS)
_SEED_IDENTITIES = tuple((pin.path, pin.bytes, pin.sha256) for pin in SEED_PINS)

# Literal identities of the actually installed Alpha-v33 parent. These bind
# data only: this tranche still needs its separate novelty and proof gates.
PARENT_CATALOG_PINS: tuple[FilePin, ...] | None = (
    FilePin("artifacts/peano-library/alpha/catalog-v33.json", 946819,
            "6be052da195a295edce02f4b1955cd9e3dd71d7acefb9ac5794277eda7ef40cc"),
    FilePin("artifacts/peano-library/alpha/catalog-v30.json", 66503303,
            "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"),
    FilePin("artifacts/peano-library/alpha/catalog-v33-delta.json", 38228899,
            "bf215f0a158b82dfb2e9e5e4a07fd7357d064b7f8a4e0230f3624b761775b1c4"),
)
PARENT_CHANNEL_PIN: FilePin | None = FilePin(
    "artifacts/peano-library/channels-v33.json", 9638,
    "d10d87694f813b86451bcccdde4dcd68e5d6fe73795b9610d98bea4f3e5de6bc")
PARENT_IDENTITY_SHA256: str | None = "9e66890600db5f787230fb5e48e18ce08026750ba4a9d3fa7b0b1e30f6e39a3d"
PARENT_ENROLLMENT_SHA256: str | None = "0d4101bfee06dfff5a49ee8cfaf955a2c81a43ac622623e27890d6fe541eeaa0"


def _require(condition, message):
    if not condition:
        raise WorkingError(message)


def _digest(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _safe_relative(value):
    return (type(value) is str and re.fullmatch(r"[A-Za-z0-9_./-]+", value) is not None
            and not value.startswith("/") and all(part not in ("", ".", "..") for part in value.split("/")))


def read_pin(pin, maximum=MAX_BYTES):
    _require(type(pin) is FilePin and _safe_relative(pin.path), "unsafe or foreign exact input pin")
    check_pin(pin, ROOT, maximum)
    raw = bounded_bytes(ROOT / pin.path, maximum)
    _require((len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256),
             "a pinned input changed during its second bounded read")
    return raw


def require_runtime_sources():
    _require(type(RUNTIME_PINS) is tuple
             and tuple((pin.path, pin.bytes, pin.sha256) for pin in RUNTIME_PINS
                       if type(pin) is FilePin) == _RUNTIME_RECORDS
             and len(RUNTIME_PINS) == len(_RUNTIME_RECORDS)
             and len(_RUNTIME_BY_PATH) == len(_RUNTIME_RECORDS),
             "the exact original runtime source inventory changed")
    for pin in RUNTIME_PINS:
        check_pin(pin, ROOT, MAX_SOURCE_BYTES)
    for folder in ("kernel", "engine"):
        actual = {path.relative_to(ROOT).as_posix()
                  for path in (ROOT / "peano-lab/py/peano_lab" / folder).glob("*.py")}
        expected = {pin.path for pin in RUNTIME_PINS
                    if pin.path.startswith("peano-lab/py/peano_lab/" + folder + "/")}
        _require(actual == expected, "an original kernel/engine source was added or removed")


def _archive_records(relative):
    _require(relative in {row[0] for row in _ARCHIVE_IDENTITIES},
             "only the two literal historical working archives may be read")
    directory = ROOT / relative
    _require(stat.S_ISDIR(directory.lstat().st_mode), "a historical archive became a symlink")
    records = []
    for path in sorted(directory.rglob("*")):
        if path.suffix not in {".py", ".md", ".txt", ".json"}:
            continue
        raw = bounded_bytes(path, MAX_BYTES)
        records.append([path.relative_to(ROOT).as_posix(), len(raw), sha256(raw).hexdigest()])
    return records


def require_preserved_archives():
    _require(type(PRESERVED_ARCHIVES) is tuple and PRESERVED_ARCHIVES == _ARCHIVE_IDENTITIES,
             "the two immutable prior working archive identities changed")
    for relative, count, expected in PRESERVED_ARCHIVES:
        records = _archive_records(relative)
        _require(len(records) == count and sha256(canonical(records)).hexdigest() == expected,
                 "a historical working archive changed: " + relative)


def require_working_sources():
    _require(type(FACTORIES) is tuple and len(FACTORIES) == 2
             and all(type(owner) is Factory for owner in FACTORIES)
             and tuple(asdict(owner) for owner in FACTORIES) == _FACTORY_RECORDS
             and tuple(owner.count for owner in FACTORIES) == (15, 10),
             "the exact frozen15+10 source ownership changed")
    for owner in FACTORIES:
        read_pin(owner.source, MAX_SOURCE_BYTES)
        read_pin(owner.test, MAX_SOURCE_BYTES)


def _edition_bindings():
    return {name: module for name, module in sys.modules.items()
            if name.startswith("peano_lab.library.editions_v")}


@dataclass(frozen=True, slots=True)
class CandidateState:
    rows: tuple[TheoremSpec, ...]
    specs_sha256: str


def load_candidate_state():
    require_working_sources()
    require_runtime_sources()
    before = _edition_bindings()
    rows = []
    for owner in FACTORIES:
        raw, path = read_pin(owner.source, MAX_SOURCE_BYTES), ROOT / owner.source.path
        alias = "_working_shift_scalar_v1_" + owner.module
        _require(alias not in sys.modules, "a private source-construction name is already owned")
        module = ModuleType(alias)
        module.__file__, module.__package__ = str(path), ""
        # No sys.modules assignment and no future peano_lab alias occur.
        exec(compile(raw, str(path), "exec"), module.__dict__)
        factory = getattr(module, owner.factory, None)
        _require(callable(factory) and getattr(factory, "__module__", None) == alias,
                 "an exact private mathematical factory is missing")
        values = factory(TheoremSpec)
        _require(type(values) is tuple and len(values) == owner.count
                 and all(type(row) is TheoremSpec for row in values)
                 and closure._specs_digest(values) == owner.specs_sha256,
                 "a frozen factory changed its actual ordered specifications")
        _require(read_pin(owner.source, MAX_SOURCE_BYTES) == raw,
                 "a mathematical source changed during factory execution")
        rows.extend(values)
    after = _edition_bindings()
    _require(before.keys() == after.keys()
             and all(after[name] is value for name, value in before.items()),
             "source construction imported or replaced an Alpha edition")
    state = CandidateState(tuple(rows), closure._specs_digest(tuple(rows)))
    validate_state(state)
    return state


def validate_state(state):
    _require(type(state) is CandidateState and type(state.rows) is tuple
             and len(state.rows) == EXPECTED_COUNT
             and all(type(row) is TheoremSpec for row in state.rows)
             and state.specs_sha256 == SPECS_SHA256
             and closure._specs_digest(state.rows) == SPECS_SHA256,
             "an altered or incomplete frozen25 syntax state is not accepted")
    closure._validate_frontier(state.rows)
    table, seen = {row.name: row for row in state.rows}, set()
    for row in state.rows:
        _require((set(row.dependencies) & table.keys()) <= seen,
                 "new source order has a forward or cyclic prerequisite")
        seen.add(row.name)
    _require(tuple(sha256(table[name].statement.encode()).hexdigest()
                   for name in PRINCIPAL_ROOTS if name in table) == PRINCIPAL_STATEMENT_SHA256
             and len(PRINCIPAL_ROOTS) == 7 and len(set(PRINCIPAL_ROOTS)) == 7,
             "the seven exact original principal statements changed")


def canonical_provider_table():
    """Actual selected source factories, not the current4092 edition."""
    require_runtime_sources()
    before = _edition_bindings()
    table = {row.name: row for row in THEOREMS}
    _require(len(table) == len(THEOREMS), "the literal primitive theorem ladder has duplicate names")
    for short in PROVIDER_MODULES:
        path = "peano-lab/py/peano_lab/library/" + short + ".py"
        _require(path in _RUNTIME_BY_PATH, "an unregistered inherited provider was requested")
        module = import_module("peano_lab.library." + short)
        _require(type(module) is ModuleType and getattr(module, "__file__", None) == str(ROOT / path)
                 and getattr(getattr(module, "__spec__", None), "origin", None) == str(ROOT / path),
                 "a canonical inherited module resolved to a foreign source")
        factory = getattr(module, "make_" + short + "_theorems", None)
        _require(callable(factory) and factory.__module__ == "peano_lab.library." + short,
                 "an inherited source factory was replaced")
        rows = factory(TheoremSpec)
        _require(type(rows) is tuple and all(type(row) is TheoremSpec for row in rows),
                 "an inherited source provider returned non-specification data")
        for row in rows:
            _require(row.name not in table or table[row.name] == row,
                     "different inherited specifications share a name")
            table[row.name] = row
    after = _edition_bindings()
    _require(before.keys() == after.keys()
             and all(after[name] is value for name, value in before.items()),
             "minimal source planning unexpectedly imported an Alpha edition")
    return table


@dataclass(frozen=True, slots=True)
class SupportSelection:
    owned: tuple[TheoremSpec, ...]
    support: tuple[TheoremSpec, ...]
    complete_specs: tuple[TheoremSpec, ...]
    root_names: tuple[str, ...]

    def role(self, name):
        if name in {row.name for row in self.owned}:
            return "new_non_admitted_shift_scalar"
        if name in {row.name for row in self.support}:
            return "inherited_canonical_source"
        if name in {row.name for row in self.complete_specs}:
            return "new_non_admitted_cross_support"
        raise WorkingError("the requested theorem is outside this exact source cone")


def select_support(state, owned_names=None):
    validate_state(state)
    all_new = {row.name: row for row in state.rows}
    if owned_names is None:
        owned_names = tuple(all_new)
    _require(type(owned_names) is tuple and bool(owned_names)
             and all(type(name) is str for name in owned_names)
             and len(set(owned_names)) == len(owned_names) and set(owned_names) <= all_new.keys()
             and owned_names == tuple(name for name in all_new if name in owned_names),
             "only a nonempty, distinct, source-ordered working selection is allowed")
    inherited_table = canonical_provider_table()
    _require(not inherited_table.keys() & all_new.keys(), "a working theorem overwrites a canonical source name")
    table = inherited_table | all_new
    ordered, active, seen = [], set(), set()

    def visit(name):
        _require(name in table, "missing actual source prerequisite: " + name)
        _require(name not in active, "cyclic actual source prerequisite: " + name)
        if name in seen:
            return
        active.add(name)
        row = table[name]
        _require(type(row.dependencies) is tuple and len(set(row.dependencies)) == len(row.dependencies),
                 "an inherited ordered premise list repeats a dependency")
        for dependency in row.dependencies:
            visit(dependency)
        active.remove(name)
        seen.add(name)
        ordered.append(row)

    for name in owned_names:
        visit(name)
    _require(len(ordered) + 1 <= closure.DEFAULT_BUNDLE_LIMITS.max_nodes,
             "the complete syntax cone exceeds the original node ceiling")
    used = {dependency for row in ordered for dependency in row.dependencies}
    roots = tuple(name for name in owned_names if name not in used)
    _require(bool(roots), "the selected source graph has no maximal working theorem")
    _require(sum(len(row.dependencies) for row in ordered) + len(roots)
             <= closure.DEFAULT_BUNDLE_LIMITS.max_edges, "the original edge ceiling was exceeded")
    selected = SupportSelection(tuple(all_new[name] for name in owned_names),
        tuple(row for row in ordered if row.name in inherited_table), tuple(ordered), roots)
    if owned_names == tuple(all_new):
        _require(len(selected.support) == EXPECTED_INHERITED_COUNT
                 and len(selected.complete_specs) == 207,
                 "the exact182 inherited +25 working source cone changed")
    return selected


@dataclass(frozen=True, slots=True)
class ExecutionSelection:
    source: SupportSelection
    frontier: tuple[TheoremSpec, ...]
    plan: closure.BottomLayerPlan


def execution_selection(state, owned_names=None):
    """The unchanged assembler's sealed-v30 syntax load occurs only here."""
    selected = select_support(state, owned_names)
    parent = {row.name: row for row in closure.parent_snapshot().specs}
    for row in selected.complete_specs:
        if row.name in parent:
            _require(row == parent[row.name], "canonical source differs from the literal v30 premise")
    frontier = tuple(row for row in selected.complete_specs if row.name not in parent)
    plan = closure.bottom_layer_plan(frontier)
    complete = {row.name: row for row in selected.complete_specs}
    _require(set(complete) == {row.name for row in plan.rows}
             and plan.root_names == selected.root_names,
             "original assembler cone or maximal roots differ from the source-only plan")
    for row in plan.rows:
        exact = complete[row.name]
        _require(row.dependencies == exact.dependencies
                 and row.statement_sha256 == sha256(exact.statement.encode()).hexdigest(),
                 "original assembler changed an exact target or ordered premise")
    return ExecutionSelection(selected, frontier, plan)


def seed_inventory(paths):
    _require(type(paths) is tuple and bool(paths)
             and all(isinstance(path, (str, Path)) for path in paths),
             "actual seed paths must be an explicit nonempty tuple")
    _require(tuple((pin.path, pin.bytes, pin.sha256) for pin in SEED_PINS) == _SEED_IDENTITIES,
             "the three approved literal seed identities changed")
    checked = closure._validate_seeds(paths)
    result = []
    known = {ROOT / pin.path: pin for pin in SEED_PINS}
    for supplied in checked:
        path = Path(supplied).absolute()
        _require(".." not in path.parts, "a proof seed may not traverse a parent")
        if path in known:
            pin = known[path]
            read_pin(pin)
        else:
            _require(path.parent == ARTIFACT_DIRECTORY and path.name.startswith(OUTPUT_PREFIX)
                     and path.name.endswith(".json") and _safe_relative(path.relative_to(ROOT).as_posix()),
                     "an unregistered external proof seed is forbidden")
            raw = bounded_bytes(path, MAX_BYTES)
            pin = FilePin(path.relative_to(ROOT).as_posix(), len(raw), sha256(raw).hexdigest())
            read_pin(pin)
        result.append(pin)
    _require(INITIAL_SEED in result, "the genuine canonical121 artifact must be an explicit seed")
    return tuple(result)


def seed_coverage(selected, pins):
    """Inert target/premise accounting; never decode a proof body."""
    _require(type(selected) is SupportSelection and type(pins) is tuple and bool(pins)
             and all(type(pin) is FilePin for pin in pins), "exact source selection and real seed pins required")
    table = {row.name: row for row in selected.complete_specs}
    targets = {name: canonical(encode_formula(_closed_formula(row.statement))) for name, row in table.items()}
    wanted = {row.name for row in selected.support}
    index = {}
    for name in wanted:
        index.setdefault(targets[name], []).append(name)
    matched, records = set(), []
    for pin in pins:
        raw = read_pin(pin)
        value = json.loads(raw)
        _require(type(value) is list and len(value) == 4 and value[0] == "peano-lab-bundle-v1"
                 and type(value[1]) is int and type(value[3]) is list
                 and 0 < len(value[3]) <= closure.DEFAULT_BUNDLE_LIMITS.max_nodes
                 and 0 <= value[1] < len(value[3]), "a real seed has malformed inert bundle metadata")
        nodes = value[3]
        _require(all(type(node) is list and len(node) == 4 and type(node[0]) is int
                     and node[0] > 0 and type(node[2]) is list
                     and all(type(edge) is int and 0 <= edge < position for edge in node[2])
                     for position, node in enumerate(nodes))
                 and value[2] == nodes[value[1]][1], "a real seed has malformed ordered target metadata")
        encoded = tuple(canonical(node[1]) for node in nodes)
        covered = set()
        for position, node in enumerate(nodes):
            for name in index.get(encoded[position], ()):
                if tuple(encoded[edge] for edge in node[2]) == tuple(targets[dep] for dep in table[name].dependencies):
                    covered.add(name)
        records.append({**asdict(pin), "inert_nodes": len(nodes),
                        "covered_targets": len(covered), "newly_covered_names": sorted(covered - matched)})
        matched.update(covered)
        check_pin(pin, ROOT, MAX_BYTES)
    return {"inherited_targets": len(wanted), "covered_targets": len(matched),
            "missing_names": sorted(wanted - matched), "seeds": records,
            "raw_json_only": True, "proof_bodies_decoded": False,
            "original_ha_checked": False, "proof_authority": False}


def require_parent_registration():
    expected_paths = ("artifacts/peano-library/alpha/catalog-v33.json",
                      closure.PARENT_CATALOG, "artifacts/peano-library/alpha/catalog-v33-delta.json")
    _require(type(PARENT_CATALOG_PINS) is tuple and len(PARENT_CATALOG_PINS) == 3
             and all(type(pin) is FilePin for pin in PARENT_CATALOG_PINS)
             and tuple(pin.path for pin in PARENT_CATALOG_PINS) == expected_paths
             and type(PARENT_CHANNEL_PIN) is FilePin
             and PARENT_CHANNEL_PIN.path == "artifacts/peano-library/channels-v33.json"
             and _digest(PARENT_IDENTITY_SHA256) and _digest(PARENT_ENROLLMENT_SHA256),
             "actual current-v33 catalogue/channel/identity pins have not been registered")
    for pin in (*PARENT_CATALOG_PINS, PARENT_CHANNEL_PIN):
        check_pin(pin, ROOT, MAX_CATALOG_BYTES)
    from peano_catalog_shards_v33 import verify_catalog_bindings
    actual = verify_catalog_bindings(ROOT / PARENT_CATALOG_PINS[0].path,
                                     expected_sha256=PARENT_CATALOG_PINS[0].sha256)
    _require(tuple((row.path.relative_to(ROOT).as_posix(), row.bytes, row.sha256) for row in actual.files)
             == tuple((pin.path, pin.bytes, pin.sha256) for pin in PARENT_CATALOG_PINS),
             "the current parent is not the exact three authenticated v33 documents")
    channels = json.loads(read_pin(PARENT_CHANNEL_PIN))
    _require(channels.get("schema") == "peano-library-channels-v33"
             and channels.get("default_channel") == "stable"
             and channels.get("channels", {}).get("alpha", {}).get("artifact_path")
                 == "artifacts/peano-library/alpha/catalog-v33.json"
             and channels["channels"]["alpha"].get("checked_use_count") == 4092
             and channels["channels"]["alpha"].get("edition_identity_sha256") == PARENT_IDENTITY_SHA256
             and channels["channels"]["alpha"].get("artifact_sha256") == PARENT_CATALOG_PINS[0].sha256,
             "the registered current channel is not exact v33 with Stable default")
    return actual


def state_binding(state, *, final=False):
    _require(type(final) is bool, "the final-registration option must be a literal Boolean")
    validate_state(state)
    require_working_sources()
    require_runtime_sources()
    require_preserved_archives()
    for pin in SEED_PINS:
        check_pin(pin, ROOT, MAX_BYTES)
    check_pin(FilePin(closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES,
                      closure.PARENT_CATALOG_SHA256), ROOT, MAX_CATALOG_BYTES)
    if final:
        require_parent_registration()
    controls = []
    for name in CONTROL_FILES:
        raw = bounded_bytes(HERE / name, MAX_SOURCE_BYTES)
        controls.append((WORKING_RELATIVE + "/" + name, len(raw), sha256(raw).hexdigest()))
    return sha256(canonical({
        "controls": controls, "runtime": _RUNTIME_RECORDS,
        "factories": [asdict(owner) for owner in FACTORIES], "specs_sha256": state.specs_sha256,
        "preserved_archives": PRESERVED_ARCHIVES, "literal_seeds": _SEED_IDENTITIES,
        "original_v30_syntax": [closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES, closure.PARENT_CATALOG_SHA256],
        "current_parent": None if PARENT_CATALOG_PINS is None else [asdict(pin) for pin in PARENT_CATALOG_PINS],
        "channels": None if PARENT_CHANNEL_PIN is None else asdict(PARENT_CHANNEL_PIN),
        "current_parent_identity": PARENT_IDENTITY_SHA256,
        "current_parent_enrollment": PARENT_ENROLLMENT_SHA256,
        "ordinary_principals": list(zip(PRINCIPAL_ROOTS, PRINCIPAL_STATEMENT_SHA256, strict=True)),
        "final_registration_required": final, "stored_observations_supply_authority": False,
    })).hexdigest()


def local_manifest():
    state = load_candidate_state()
    selected = select_support(state)
    coverage = seed_coverage(selected, SEED_PINS)
    return {
        "schema": "peano-working-shift-scalar-syntax-v1", "syntax_only": True,
        "new_non_admitted_rows": 25, "factory_counts": [15, 10],
        "specs_sha256": state.specs_sha256, "ordered_names": [row.name for row in state.rows],
        "inherited_source_rows": len(selected.support), "complete_source_rows": len(selected.complete_specs),
        "new_dependency_edges": sum(len(row.dependencies) for row in state.rows),
        "new_script_commands": sum(len(row.script) for row in state.rows),
        "complete_dependency_edges": sum(len(row.dependencies) for row in selected.complete_specs),
        "maximal_roots": list(selected.root_names), "ordinary_principals": list(PRINCIPAL_ROOTS),
        "seed_coverage": coverage, "global_current4092_novelty_checked": False,
        "original_ha_checked": False, "independent_lean_checked": False,
        "ordinary_principals_checked": False, "associativity_proved": False,
        "gcd_bezout_proved": False, "full_G091_proved": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }
