"""Fail-closed audit for the native Bertrand B8 prime certificates.

The candidate rows are rebuilt over Stable plus their exact earlier local
prefix.  Public formulas are reconstructed independently, every direct edge
is required, and each empty-context proof is checked under the unchanged
resource limits before its deterministic receipt is accepted.
"""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Eq,
    Formula,
    Imp,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero, parse_term_in_context, pretty_term
from peano_lab.library import (
    alpha_enrollment_v11,
    editions_v11,
    theorems as stable_module,
)
from peano_lab.library import bertrand_b8_prime_certificates_candidate as module
from peano_lab.library import bertrand_primorial_choose_interval_candidate
from peano_lab.library import bertrand_primorial_foundation_candidate
from peano_lab.library import bertrand_primorial_membership_candidate
from peano_lab.library.bertrand_b8_prime_certificates_candidate import (
    ADD_REMAINDER_LIFT,
    DOUBLE_SCALED_REMAINDER_LIFT,
    FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE,
    FIXED_NONTRIVIAL_FACTOR_NOT_PRIME,
    NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
    NONZERO_REMAINDER_NOT_MULTIPLE,
    PRIME_EIGHTY_THREE,
    PRIME_FIVE,
    PRIME_FIVE_HUNDRED_TWENTY_ONE,
    PRIME_FORTY_THREE,
    PRIME_LE_TWENTY_TWO_CASES,
    PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
    PRIME_ONE_HUNDRED_SIXTY_THREE,
    PRIME_SEVEN,
    PRIME_THIRTEEN,
    PRIME_THREE_HUNDRED_SEVENTEEN,
    PRIME_TWENTY_THREE,
    SCALED_REMAINDER_LIFT,
    make_bertrand_b8_prime_certificate_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    _proof_envelope_metrics_bounded,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    FIXED_NONTRIVIAL_FACTOR_NOT_PRIME,
    FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE,
    NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
    PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
    PRIME_LE_TWENTY_TWO_CASES,
    NONZERO_REMAINDER_NOT_MULTIPLE,
    SCALED_REMAINDER_LIFT,
    ADD_REMAINDER_LIFT,
    DOUBLE_SCALED_REMAINDER_LIFT,
    PRIME_FIVE,
    PRIME_SEVEN,
    PRIME_THIRTEEN,
    PRIME_TWENTY_THREE,
    PRIME_FORTY_THREE,
    PRIME_EIGHTY_THREE,
    PRIME_ONE_HUNDRED_SIXTY_THREE,
    PRIME_THREE_HUNDRED_SEVENTEEN,
    PRIME_FIVE_HUNDRED_TWENTY_ONE,
)

_CERTIFICATES = (
    (PRIME_FIVE, "5", 5),
    (PRIME_SEVEN, "7", 7),
    (PRIME_THIRTEEN, "13", 13),
    (PRIME_TWENTY_THREE, "23", 23),
    (PRIME_FORTY_THREE, "43", 43),
    (PRIME_EIGHTY_THREE, "9 * 9 + 2", 83),
    (PRIME_ONE_HUNDRED_SIXTY_THREE, "13 * 12 + 7", 163),
    (PRIME_THREE_HUNDRED_SEVENTEEN, "18 * 17 + 11", 317),
    (PRIME_FIVE_HUNDRED_TWENTY_ONE, "2 * (11 * 22) + 37", 521),
)

_CERTIFICATE_DEPENDENCIES = (
    NONZERO_REMAINDER_NOT_MULTIPLE,
    PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
    "le_trans",
    PRIME_LE_TWENTY_TWO_CASES,
    "lt_not_le",
)

EXPECTED_DEPENDENCIES = {
    FIXED_NONTRIVIAL_FACTOR_NOT_PRIME: (),
    FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE: (
        "le_total",
        "le_or_lt",
        "mul_le_mul_right",
        "mul_le_mul_left",
        "le_trans",
        "lt_not_le",
    ),
    NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
        "prime_or_composite",
        FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE,
        "mul_zero_left",
        "prime_divisor_exists",
        "divisor_le_nonzero",
        "le_trans",
        "multiple_trans",
        "mul_comm",
    ),
    PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
        "prime_decidable",
        NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
    ),
    PRIME_LE_TWENTY_TWO_CASES: (
        "le_eq_or_lt",
        "le_of_succ_le_succ",
        "prime_is_succ_succ",
        "lt_not_le",
        FIXED_NONTRIVIAL_FACTOR_NOT_PRIME,
    ),
    NONZERO_REMAINDER_NOT_MULTIPLE: (
        "multiple_refl",
        "divides_remainder",
        "divisor_le_nonzero",
        "lt_not_le",
    ),
    SCALED_REMAINDER_LIFT: (
        "mul_add",
        "mul_assoc",
        "mul_comm",
        "add_assoc",
    ),
    ADD_REMAINDER_LIFT: ("mul_add", "add_assoc", "add_comm"),
    DOUBLE_SCALED_REMAINDER_LIFT: (SCALED_REMAINDER_LIFT,),
    PRIME_FIVE: _CERTIFICATE_DEPENDENCIES,
    PRIME_SEVEN: _CERTIFICATE_DEPENDENCIES,
    PRIME_THIRTEEN: _CERTIFICATE_DEPENDENCIES,
    PRIME_TWENTY_THREE: _CERTIFICATE_DEPENDENCIES,
    PRIME_FORTY_THREE: _CERTIFICATE_DEPENDENCIES,
    PRIME_EIGHTY_THREE: (
        "add_eq_zero_right",
        "le_not_lt",
        "add_assoc",
        "add_comm",
        "mul_succ_left",
        SCALED_REMAINDER_LIFT,
        *_CERTIFICATE_DEPENDENCIES,
    ),
    PRIME_ONE_HUNDRED_SIXTY_THREE: (
        "add_eq_zero_right",
        "le_not_lt",
        "add_assoc",
        "add_comm",
        SCALED_REMAINDER_LIFT,
        *_CERTIFICATE_DEPENDENCIES,
    ),
    PRIME_THREE_HUNDRED_SEVENTEEN: (
        "add_eq_zero_right",
        "le_not_lt",
        "add_assoc",
        "add_comm",
        SCALED_REMAINDER_LIFT,
        *_CERTIFICATE_DEPENDENCIES,
    ),
    PRIME_FIVE_HUNDRED_TWENTY_ONE: (
        "add_eq_zero_right",
        "le_not_lt",
        "add_assoc",
        "add_comm",
        DOUBLE_SCALED_REMAINDER_LIFT,
        "add_mul",
        "mul_assoc",
        "one_mul",
        *_CERTIFICATE_DEPENDENCIES[:-1],
    ),
}

EXPECTED_DIRECT_CUTS = {
    name: len(EXPECTED_DEPENDENCIES[name]) for name in EXPECTED_NAMES
}

EXPECTED_ARTIFACTS = {
    FIXED_NONTRIVIAL_FACTOR_NOT_PRIME: (
        244,
        "ddf96a4f1160b662b9519eca77a9a58df92f37a656171b3dac8250cc1f664347",
        "be45994e084a2e884762c01afd3162ba1774f6aefca1cf2cceafdbecf570af8a",
        "ddf96a4f1160b662b9519eca77a9a58df92f37a656171b3dac8250cc1f664347",
    ),
    FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE: (
        244,
        "3f1bc05c640a8d40a7915dcf4cae14e01bbccac834ce641e7cb40e1c687ea0e9",
        "ab3440bbf20ab6f9a87e56520de93a56862a8aa700557d61808486fc2d120938",
        "c81469bfe28b776815a5e354acc55ad6063c4a509b3821e9e5d07744722786cc",
    ),
    NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
        664,
        "0e1317e8a9a57ff9fbc15f1ff336f06f338d5bd5f567e00447caf302f18f0ba9",
        "cb4129febc6360797bf55a7a6c34011277da3d94913447e75a5dcdc183e5e699",
        "aa955d9d6e9a32833e15da0e711880c23235fc183f0cdf04d6cb762a82b18a73",
    ),
    PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
        662,
        "819b8b9c1c1f7cb5502b46b0d31d488c4c6be7a8d9f6d8610351c4c4a43a9043",
        "71e7e71f2ba6911c467a4fa7c4718b8099ef02aaf102cbff6518e5300cf4c495",
        "ed8b46d010b12acd9a5bdddbf0f655a3a5cf1be8f96d94e9918e7bb0e5af855f",
    ),
    PRIME_LE_TWENTY_TWO_CASES: (
        354,
        "9dc7e921dd7678726eccf926f755a815235876da57a54a7de3e569d91d0c0279",
        "3619394d7bbf34cd6cce585806264632747986b9a44917411250b556064efaae",
        "f25a260cd38537e492f1a5d2dd81350cc30d8f366c37f751df6c921da482a59c",
    ),
    NONZERO_REMAINDER_NOT_MULTIPLE: (
        178,
        "571bdd24f3087c96956d47d4d439d6485375cd3cec95e9b967fcbbf13df59f48",
        "360eb4a629dbdef5ba2e6bb29ca66f4c4377d6564628a3a7d8c70601b8b41b0c",
        "3db3f867bdc43a758a454e6a4e0f9739d4c718beecb21bfe350668a25639b62d",
    ),
    SCALED_REMAINDER_LIFT: (
        97,
        "45ad77e963d5a07fed2ced871368979fbeabbcdee0842893b6fd98b4599c867a",
        "83214ec7d6495eb6d88794db391444abd63e714452e27b5919a063b64f813dea",
        "d84faa6d4aead73fa9792ff1c6328e6cf5b78a06001c50eb997f4f47fac3b05e",
    ),
    ADD_REMAINDER_LIFT: (
        110,
        "9859e3b1f1c0e8500e8e14d31e0ea3234df04c30355ad5106a58310735e60858",
        "48cc17c3fdd6e027023f505132fd424ee463d2a87e6a53d7cf5fd25ce4677f8a",
        "7702fc64e3eb3ae577e118af07776bdbee6f434a0d97523c2a410ec5f14ed7b6",
    ),
    DOUBLE_SCALED_REMAINDER_LIFT: (
        139,
        "01060b288299af742c54b0fba6abbee26eecb49ae441d989562d99de8296720e",
        "326393fbf402c0c23a00a9e6fc3efc6fed31efef5968e91588c0dbece2d774f1",
        "9013bce63f632bf78bde7e6f83a738566567db32bd3023e477135db52e560576",
    ),
    PRIME_FIVE: (
        212,
        "901d0637312adda5aaf07c502afa5e847c7f2a06ee47464ae09a023bc9d48878",
        "784871bce6e388dd403d5c12cb8dfb8c6014f42360b85e973ca7b7e0191d6ca6",
        "9a9f529b739e8c6ec5b3eff3ec2146c81d13ca30d9e806ed704c816a2c16f68b",
    ),
    PRIME_SEVEN: (
        218,
        "12ecfd5e25572281c9edd2e61f83728fb67e951beea96a25d3876d1d16bcf913",
        "047d1f93b81ee2606df0bc4c65a65524f7ea1378ec160e51ef768da4e6a4a5a8",
        "748ac4318fc825be98a4676863c705d8e771c7743449ec030f09c13ed379ebf5",
    ),
    PRIME_THIRTEEN: (
        238,
        "5a03cdd0f0056d15b952dd02ebcde68928ba61ebdc9e76167ac96bbcd1f9e7c4",
        "2493c286e31b841f1884428ab30b452abc6dadebbc96ad989ef9198f0b372f36",
        "b34cb0127246720ef8d434d85593a7a98e5430569563044c80b88e89eba63542",
    ),
    PRIME_TWENTY_THREE: (
        262,
        "1e660ae883cbd055fdaf72366927a99dc9d6f5a8bfe9aca8a24a7971efd955c5",
        "950510a971372b24528ba81fb02fd5b0ca076e2956476c956f5b05d3e9d2b072",
        "5cde19f301ff3d06146fd6e4a0e27684caf591b96eddf27458e0ccc296ad09b5",
    ),
    PRIME_FORTY_THREE: (
        256,
        "65a6bcb1e50e54b40db08d82b72022f0c9b3ea880a54c7030641ab722b0f69cf",
        "547fa0260cd7e2cdd1ed895c78966d30de116fea4eafe9be6d2f1f7d986cb681",
        "5f343e1e625179816d94aaa6daefbf7a2df160bf4d522f8e33ac430354de915b",
    ),
    PRIME_EIGHTY_THREE: (
        276,
        "7c1fe496965631bfe7d38563c1b79a4ba48563e5419c507efe1132393f9f6ec0",
        "02ed476556316f94d6214edffa14d51669c637946ec582889ff1dd072fcfdc56",
        "824f943d9d30b8f45822725388b178d47c0b74bd30d771a2f9b26028eccd531a",
    ),
    PRIME_ONE_HUNDRED_SIXTY_THREE: (
        346,
        "98fbb643ee0e0286fa0a253ae84c1b33e236cd6d0f073a48d2c62bbb6e59ee92",
        "2aac16844a9cabdcec7efda88101ac7d1568586ad54ef41d69592c439daa0f98",
        "df0cd0bb005075bada7bcdc48ecfcafbcabc118414c7eb771c94952cf2e0199b",
    ),
    PRIME_THREE_HUNDRED_SEVENTEEN: (
        348,
        "13598b99bb504c798727e54301b14c15233806dc2486c0d609874dc21b1c796f",
        "532234c275df3e0d9a3b5c537fdadc310aa2467e3ce40c65e42e22bb87d11e96",
        "763e844a3b5a78aebc964402c2a0ece8d4337353d285e9b4ff63e7bc78a3a770",
    ),
    PRIME_FIVE_HUNDRED_TWENTY_ONE: (
        360,
        "9c65ead8aa1a0fe709c359a41506fde85ae21fdcd59967c61ff572b2faefb9a8",
        "ef88b81326ed4108ecaf79e9481441dfa071c21441197f240d5ba87f7f79c10e",
        "326a320fbccc67fa0bfb0f76e626bc85a8a1dcdb2b1037bf72647ea9f897db22",
    ),
}

EXPECTED_BODIES = {
    FIXED_NONTRIVIAL_FACTOR_NOT_PRIME: (0, 18, 20, 13, 20, 19, 0),
    FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE: (6, 91, 98, 26, 98, 97, 0),
    NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
        8, 106, 172, 33, 170, 171, 2,
    ),
    PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
        2, 26, 38, 18, 38, 37, 0,
    ),
    PRIME_LE_TWENTY_TWO_CASES: (5, 473, 2391, 57, 2391, 2390, 0),
    NONZERO_REMAINDER_NOT_MULTIPLE: (4, 32, 37, 23, 37, 36, 0),
    SCALED_REMAINDER_LIFT: (4, 39, 61, 26, 61, 60, 0),
    ADD_REMAINDER_LIFT: (3, 50, 71, 27, 71, 70, 0),
    DOUBLE_SCALED_REMAINDER_LIFT: (1, 38, 45, 26, 45, 44, 0),
    PRIME_FIVE: (5, 120, 658, 40, 658, 657, 0),
    PRIME_SEVEN: (5, 120, 688, 40, 688, 687, 0),
    PRIME_THIRTEEN: (5, 124, 995, 44, 995, 994, 0),
    PRIME_TWENTY_THREE: (5, 124, 1331, 60, 1331, 1330, 0),
    PRIME_FORTY_THREE: (5, 128, 2344, 100, 2344, 2343, 0),
    PRIME_EIGHTY_THREE: (11, 215, 2379, 62, 2379, 2378, 0),
    PRIME_ONE_HUNDRED_SIXTY_THREE: (
        10, 224, 3436, 75, 3436, 3435, 0,
    ),
    PRIME_THREE_HUNDRED_SEVENTEEN: (
        10, 256, 7283, 84, 7283, 7282, 0,
    ),
    PRIME_FIVE_HUNDRED_TWENTY_ONE: (
        12, 287, 11070, 107, 11070, 11069, 0,
    ),
}

EXPECTED_ENVELOPES = {
    FIXED_NONTRIVIAL_FACTOR_NOT_PRIME: (20, 20, 13, 2, 13),
    FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE: (98, 98, 26, 88, 27),
    NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (172, 170, 33, 57, 33),
    PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (38, 38, 18, 4, 18),
    PRIME_LE_TWENTY_TWO_CASES: (2391, 2391, 57, 4237, 57),
    NONZERO_REMAINDER_NOT_MULTIPLE: (37, 37, 23, 10, 23),
    SCALED_REMAINDER_LIFT: (61, 61, 26, 125, 27),
    ADD_REMAINDER_LIFT: (71, 71, 27, 140, 28),
    DOUBLE_SCALED_REMAINDER_LIFT: (45, 45, 26, 129, 55),
    PRIME_FIVE: (658, 658, 40, 1141, 46),
    PRIME_SEVEN: (688, 688, 40, 1192, 46),
    PRIME_THIRTEEN: (995, 995, 44, 1944, 47),
    PRIME_TWENTY_THREE: (1331, 1331, 60, 3266, 61),
    PRIME_FORTY_THREE: (2344, 2344, 100, 9492, 105),
    PRIME_EIGHTY_THREE: (2379, 2379, 62, 5967, 77),
    PRIME_ONE_HUNDRED_SIXTY_THREE: (3436, 3436, 75, 12533, 111),
    PRIME_THREE_HUNDRED_SEVENTEEN: (7283, 7283, 84, 43182, 159),
    PRIME_FIVE_HUNDRED_TWENTY_ONE: (11070, 11070, 107, 49993, 145),
}

EXPECTED_CLOSURES = {
    FIXED_NONTRIVIAL_FACTOR_NOT_PRIME: (
        20, 13, 20, 19, 0, 2, 13,
        "2dcfb27df1dac26cbacc36d502f4da7b05399fdd5b58af41a7d3205e3e7fe047",
    ),
    FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE: (
        745, 29, 570, 604, 35, 1965, 30,
        "63b62b6c4d4c4f84559f94fe5a9cbd70d10ecd72ba5ae74027adce2f5b580a64",
    ),
    NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
        6433, 84, 2196, 2300, 105, 17232, 84,
        "02f699a7c67920684706c154dfcfdbb563d9fb28d81936c9f0c311d3d5630b78",
    ),
    PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
        8665, 86, 2320, 2428, 109, 23177, 86,
        "d8a6dbdaace94880c7bcdee36a4ac4ed3c432924b9d6de553fcb3c2101233c62",
    ),
    PRIME_LE_TWENTY_TWO_CASES: (
        2679, 57, 2674, 2678, 5, 5725, 57,
        "71b9e37f4254051e67245239f7027a296ffb254d68fbbb75ecc9bac514bb64b8",
    ),
    NONZERO_REMAINDER_NOT_MULTIPLE: (
        623, 31, 530, 558, 29, 1546, 31,
        "2f041ee581fd96683f50d08049f41cc6fdf049c5641d00e39bb2591772fb457c",
    ),
    SCALED_REMAINDER_LIFT: (
        509, 27, 333, 368, 36, 1597, 28,
        "65249ffe26d82c16a7147ba95e6ea8fdbe9ed4e7545a0ec5c8dbd9c65df84b12",
    ),
    ADD_REMAINDER_LIFT: (
        254, 27, 206, 221, 16, 809, 28,
        "f2e07d100bf16270ad9a547553941b1e0ae0b997e6574783c325722fdd5d9e74",
    ),
    DOUBLE_SCALED_REMAINDER_LIFT: (
        554, 28, 378, 413, 36, 1941, 55,
        "9769bfcd406ec29c7e3cbd03f373a4bfb8a9b5b268b693606c9e8015a12c4641",
    ),
    PRIME_FIVE: (
        12738, 88, 5603, 5726, 124, 32294, 88,
        "b8be0139b05ae90e69d3f9d065cab9b74c47b4df6515181433ea8d27a1575f44",
    ),
    PRIME_SEVEN: (
        12768, 88, 5633, 5756, 124, 32365, 88,
        "7c84b32385d1daf8c302bd388e11427c7ca662bfda02eadf8e14ef641541a144",
    ),
    PRIME_THIRTEEN: (
        13075, 88, 5940, 6063, 124, 33177, 88,
        "58fb6aafcb9836a83ea1a4022e3a022e9883a8a2075bcadbec1f1093da027511",
    ),
    PRIME_TWENTY_THREE: (
        13411, 88, 6276, 6399, 124, 34599, 88,
        "37148af189aa7043923f1d8ba060f345d87e24b0b14d1f129f57e0d81c21605e",
    ),
    PRIME_FORTY_THREE: (
        14424, 100, 7289, 7412, 124, 41025, 105,
        "948c8dfbdba7c38564704ff21dca5495abd942d72dee8c808c8accd9bd005ced",
    ),
    PRIME_EIGHTY_THREE: (
        15339, 94, 7403, 7535, 133, 40256, 94,
        "16a866941aaea108a6dbc2bb024f8c39271c36f34d7caaa559fefecac7672f55",
    ),
    PRIME_ONE_HUNDRED_SIXTY_THREE: (
        16224, 93, 8460, 8591, 132, 46534, 111,
        "33da853e9295950f30550b1bff8d3541f51c5c66de54cf109a023da7c918234f",
    ),
    PRIME_THREE_HUNDRED_SEVENTEEN: (
        20071, 93, 12307, 12438, 132, 77463, 159,
        "ff604c25b877d7103278e0f55839ebaa9db27e5f6da4e707738f05e6bcbecd48",
    ),
    PRIME_FIVE_HUNDRED_TWENTY_ONE: (
        24315, 107, 16161, 16297, 137, 86943, 145,
        "9cc6d0a577111a5c7e99702c7314eea5705262236adc1eb374a2fda7ba6e58de",
    ),
}

SOURCE_PINS = {
    "peano-lab/py/peano_lab/library/theorems.py":
        "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v11.py":
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093",
    "peano-lab/py/peano_lab/library/editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_primorial_choose_interval_candidate.py"
    ): "5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_primorial_foundation_candidate.py"
    ): "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_primorial_membership_candidate.py"
    ): "edf14adde5edbbc6b7836003a174ee9a4b84f708fdcd0f3c3af45fc5013ac817",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_b8_prime_certificates_candidate.py"
    ): "e38954201d57680644ec6353d7d4c25b320f720d36f07c1c32d590c7920d3387",
}

RFC_PINS = {
    (
        "research/arithmetic-library/"
        "ha-bertrand-postulate-campaign-rfc-v1.md"
    ): "0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b",
    (
        "research/arithmetic-library/"
        "ha-bertrand-postulate-campaign-rfc-v2.md"
    ): "af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b8-prime-certificates-tranche-rfc-v1.md"
    ): "356e8d69498f117921b1229c9a07b42f9caad48febe612a2e89ab93578a3ba73",
}

_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _context(variables: tuple[str, ...]) -> tuple[str, ...]:
    assert isinstance(variables, tuple)
    assert len(set(variables)) == len(variables)
    for value in variables:
        assert value and value not in _RESERVED
        assert value[0].isalpha() or value[0] == "_"
        assert all(character.isalnum() or character in "_'" for character in value)
    return variables


def _render(source: str, variables: tuple[str, ...]) -> str:
    context = _context(variables)
    term = parse_term_in_context(source, list(context))
    return pretty_term(term, list(context)).replace("·", "*")


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    assert tag and tag not in _RESERVED and " " not in tag
    names = tuple(f"bpr_{stem}_{tag}" for stem in stems)
    assert not set(names) & set(variables)
    return names


def _prime(
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered = _render(value, context)
    left, right = _binders(tag, context, ("left", "right"))
    return (
        f"(~({rendered} = 1) /\\ forall {left} {right}. "
        f"{rendered} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def _lt(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_left = _render(left, context)
    rendered_right = _render(right, context)
    (gap,) = _binders(tag, context, ("gap",))
    return f"exists {gap}. {gap} + S ({rendered_left}) = {rendered_right}"


def _le(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_left = _render(left, context)
    rendered_right = _render(right, context)
    (gap,) = _binders(tag, context, ("le_gap",))
    return f"exists {gap}. {gap} + ({rendered_left}) = ({rendered_right})"


def _divides(
    divisor: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_divisor = _render(divisor, context)
    rendered_value = _render(value, context)
    (quotient,) = _binders(tag, context, ("quotient",))
    return (
        f"exists {quotient}. {rendered_value} = "
        f"({rendered_divisor}) * {quotient}"
    )


def _prime_cases_result(p: str, values: tuple[int, ...] = (
    2, 3, 5, 7, 11, 13, 17, 19,
)) -> str:
    result = f"{p} = {values[-1]}"
    for value in reversed(values[:-1]):
        result = f"{p} = {value} \\/ ({result})"
    return result


def _surface_parts() -> dict[str, str]:
    factor_variables = ("n", "a", "b")
    small_variables = ("B", "n", "a", "b")
    divisor_variables = ("B", "n")
    cases_variables = ("p",)
    remainder_variables = ("d", "n", "q", "r")
    return {
        "factor_prime": _prime(
            "n", tag="bb8fnfp_prime", variables=factor_variables
        ),
        "small_bound": _lt(
            "n", "S B * S B", tag="bb8fps_bound", variables=small_variables
        ),
        "small_left": _le(
            "a", "B", tag="bb8fps_left", variables=small_variables
        ),
        "small_right": _le(
            "b", "B", tag="bb8fps_right", variables=small_variables
        ),
        "divisor_square": _lt(
            "n", "S B * S B", tag="bb8npsp_square", variables=divisor_variables
        ),
        "divisor_source": _prime(
            "n", tag="bb8npsp_source", variables=divisor_variables
        ),
        "divisor_prime": _prime(
            "p", tag="bb8npsp_prime", variables=divisor_variables + ("p",)
        ),
        "divisor_bound": _le(
            "p", "B", tag="bb8npsp_bound", variables=divisor_variables + ("p",)
        ),
        "divisor_relation": _divides(
            "p", "n", tag="bb8npsp_divides", variables=divisor_variables + ("p",)
        ),
        "criterion_square": _lt(
            "n", "S B * S B", tag="bb8pnsp_square", variables=divisor_variables
        ),
        "criterion_result": _prime(
            "n", tag="bb8pnsp_result", variables=divisor_variables
        ),
        "criterion_test_prime": _prime(
            "p", tag="bb8pnsp_prime", variables=divisor_variables + ("p",)
        ),
        "criterion_test_bound": _le(
            "p", "B", tag="bb8pnsp_bound", variables=divisor_variables + ("p",)
        ),
        "criterion_test_divides": _divides(
            "p", "n", tag="bb8pnsp_divides", variables=divisor_variables + ("p",)
        ),
        "cases_prime": _prime(
            "p", tag="bb8p22_prime", variables=cases_variables
        ),
        "cases_bound": _le(
            "p", "22", tag="bb8p22_bound", variables=cases_variables
        ),
        "remainder_lt": _lt(
            "r", "d", tag="bb8rn_lt", variables=remainder_variables
        ),
        "remainder_divides": _divides(
            "d", "n", tag="bb8rn_divides", variables=remainder_variables
        ),
    }


def _expected_statements() -> dict[str, str]:
    part = _surface_parts()
    divisor_exists = (
        f"exists p. ({part['divisor_prime']}) /\\ "
        f"(({part['divisor_bound']}) /\\ ({part['divisor_relation']}))"
    )
    result = {
        FIXED_NONTRIVIAL_FACTOR_NOT_PRIME: (
            "forall n a b. n = a * b -> ~(a = 1) -> ~(b = 1) -> "
            f"({part['factor_prime']}) -> false"
        ),
        FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE: (
            "forall B n a b. n = a * b -> "
            f"({part['small_bound']}) -> "
            f"({part['small_left']}) \\/ ({part['small_right']})"
        ),
        NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
            "forall B n. ~(n = 0) -> ~(n = 1) -> "
            f"({part['divisor_square']}) -> ~({part['divisor_source']}) -> "
            f"({divisor_exists})"
        ),
        PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE: (
            "forall B n. ~(n = 0) -> ~(n = 1) -> "
            f"({part['criterion_square']}) -> "
            f"(forall p. ({part['criterion_test_prime']}) -> "
            f"({part['criterion_test_bound']}) -> "
            f"~({part['criterion_test_divides']})) -> "
            f"({part['criterion_result']})"
        ),
        PRIME_LE_TWENTY_TWO_CASES: (
            "forall p. "
            f"({part['cases_prime']}) -> ({part['cases_bound']}) -> "
            f"({_prime_cases_result('p')})"
        ),
        NONZERO_REMAINDER_NOT_MULTIPLE: (
            "forall d n q r. n = d * q + r -> ~(r = 0) -> "
            f"({part['remainder_lt']}) -> ~({part['remainder_divides']})"
        ),
        SCALED_REMAINDER_LIFT: (
            "forall d x q t c r s u. x = d * q + t -> "
            "c * t + r = d * s + u -> "
            "c * x + r = d * (c * q + s) + u"
        ),
        ADD_REMAINDER_LIFT: (
            "forall d x y q s r t u v. x = d * q + r -> "
            "y = d * s + t -> r + t = d * u + v -> "
            "x + y = d * ((q + s) + u) + v"
        ),
        DOUBLE_SCALED_REMAINDER_LIFT: (
            "forall d x q t s r u v. x = d * q + t -> "
            "11 * t = d * s + r -> 2 * r + 37 = d * u + v -> "
            "2 * (11 * x) + 37 = d * (2 * (11 * q + s) + u) + v"
        ),
    }
    for name, target, _number in _CERTIFICATES:
        result[name] = _prime(target, tag=f"bb8cert_{name}", variables=())
    return result


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_b8_prime_certificate_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return _specs_by_name()


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _core() | _table(_specs()[:index])


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _available()
    formula = _closed_formula(item.statement)
    target = formula
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        assert tactic != "use"
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _close(
    name: str,
    cache: dict[str, tuple[Formula, Proof]] | None = None,
) -> tuple[Formula, Proof]:
    if cache is None:
        cache = {}
    if name in cache:
        return cache[name]
    public = _specs_by_name()
    if name in public:
        checked = replay(name)
        result = (checked.formula, checked.certificate)
        cache[name] = result
        return result
    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    dependencies = tuple(_close(dependency, cache) for dependency in item.dependencies)
    for dependency_formula, dependency_proof in reversed(dependencies):
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    result = (formula, body)
    cache[name] = result
    return result


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_proof(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(_proof_children(node))


def _proof_dag_sha256(proof: Proof) -> str:
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


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_b8_prime_certificate_sources_and_contracts_are_pinned() -> None:
    providers = {
        stable_module: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/theorems.py"
        ],
        alpha_enrollment_v11: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/alpha_enrollment_v11.py"
        ],
        editions_v11: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/editions_v11.py"
        ],
        bertrand_primorial_choose_interval_candidate: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/"
            "bertrand_primorial_choose_interval_candidate.py"
        ],
        bertrand_primorial_foundation_candidate: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/"
            "bertrand_primorial_foundation_candidate.py"
        ],
        bertrand_primorial_membership_candidate: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/"
            "bertrand_primorial_membership_candidate.py"
        ],
        module: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/"
            "bertrand_b8_prime_certificates_candidate.py"
        ],
    }
    for provider, digest in providers.items():
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest
    root = _repository_root()
    for relative, digest in RFC_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest


def test_b8_prime_certificate_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    expected_statements = _expected_statements()
    stable = _core()
    alpha_names = {row.name for row in editions_v11.ALPHA_SPECS}
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert not set(EXPECTED_NAMES) & set(stable)
    assert not set(EXPECTED_NAMES) & alpha_names
    assert sum(EXPECTED_DIRECT_CUTS.values()) == 101
    assert tuple(EXPECTED_DIRECT_CUTS.values()) == (
        0, 6, 8, 2, 5, 4, 4, 3, 1, 5, 5, 5, 5, 5, 11, 10, 10, 12,
    )
    for row in rows:
        assert row.statement == expected_statements[row.name]
        assert row.dependencies == EXPECTED_DEPENDENCIES[row.name]
        parsed, free_names = parse_formula_with_names(row.statement)
        assert isinstance(parsed, Formula)
        assert not free_names
        assert parsed == _closed_formula(row.statement)
    assert tuple(module.__all__) == (
        "FIXED_NONTRIVIAL_FACTOR_NOT_PRIME",
        "FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE",
        "NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE",
        "PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE",
        "PRIME_LE_TWENTY_TWO_CASES",
        "NONZERO_REMAINDER_NOT_MULTIPLE",
        "SCALED_REMAINDER_LIFT",
        "ADD_REMAINDER_LIFT",
        "DOUBLE_SCALED_REMAINDER_LIFT",
        "PRIME_FIVE",
        "PRIME_SEVEN",
        "PRIME_THIRTEEN",
        "PRIME_TWENTY_THREE",
        "PRIME_FORTY_THREE",
        "PRIME_EIGHTY_THREE",
        "PRIME_ONE_HUNDRED_SIXTY_THREE",
        "PRIME_THREE_HUNDRED_SEVENTEEN",
        "PRIME_FIVE_HUNDRED_TWENTY_ONE",
        "make_bertrand_b8_prime_certificate_candidate_theorems",
    )


def test_b8_prime_certificate_scripts_are_exact_and_constructive() -> None:
    forbidden = (
        "DNE",
        "by_contra",
        "classical",
        "compact_arith",
        "ring",
        "simp",
        "sorry",
        "use ",
    )
    rows = _table(_specs())
    for name in EXPECTED_NAMES:
        row = rows[name]
        assert len(row.script) == EXPECTED_BODIES[name][1]
        assert not any(
            token in command
            for command in row.script
            for token in forbidden
        )
        assert not any(command.startswith("induction ") for command in row.script)
    assert rows[PRIME_LE_TWENTY_TWO_CASES].script.count("norm_num") == 13
    for name, _target, number in _CERTIFICATES:
        row = rows[name]
        assert not any(
            command.startswith("have hnotdivides_")
            for command in row.script
        )
        expected_trials = sum(prime <= {
            5: 2, 7: 2, 13: 3, 23: 4, 43: 6,
            83: 9, 163: 12, 317: 17, 521: 22,
        }[number] for prime in (2, 3, 5, 7, 11, 13, 17, 19))
        assert row.script.count(
            f"apply {NONZERO_REMAINDER_NOT_MULTIPLE}"
        ) == expected_trials
    assert rows[PRIME_FIVE_HUNDRED_TWENTY_ONE].script.count(
        f"apply {DOUBLE_SCALED_REMAINDER_LIFT}"
    ) == 8


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_b8_prime_certificate_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256("\0".join((item.statement, *item.dependencies)).encode()).hexdigest(),
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_b8_prime_certificate_bodies_and_envelopes_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    body, target = _body(item)
    assert check((), body, target)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        body,
        max_proof_occurrences=limits.max_body_occurrences,
        max_proof_objects=limits.max_body_objects,
        max_proof_depth=limits.max_body_depth,
        max_annotation_occurrences=limits.max_body_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_body_envelope_depth,
        label=f"B8 certificate body {name}",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual = (
        len(item.dependencies), len(item.script), nodes, depth,
        objects, edges, reused,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == len(set(LIVE_EDGES)) == 101


@pytest.mark.parametrize(
    ("name", "dependency"),
    LIVE_EDGES,
    ids=tuple(f"{name}--{dependency}" for name, dependency in LIVE_EDGES),
)
def test_b8_prime_certificate_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(
            candidate
            for candidate in item.dependencies
            if candidate != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_b8_prime_certificate_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    part = _surface_parts()
    small_result = f"({part['small_left']}) \\/ ({part['small_right']})"
    small_both = f"({part['small_left']}) /\\ ({part['small_right']})"
    cases_result = _prime_cases_result("p")
    cases_without_19 = _prime_cases_result("p", (2, 3, 5, 7, 11, 13, 17))
    mutations = [
        (
            FIXED_NONTRIVIAL_FACTOR_NOT_PRIME,
            "allow_right_unit",
            "~(b = 1)",
            "b = 1",
        ),
        (
            FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE,
            "require_both_small",
            small_result,
            small_both,
        ),
        (
            NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
            "successor_prime_bound",
            part["divisor_bound"],
            _le(
                "S p",
                "B",
                tag="bb8npsp_bound",
                variables=("B", "n", "p"),
            ),
        ),
        (
            PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
            "successor_primality",
            part["criterion_result"],
            _prime(
                "S n",
                tag="bb8pnsp_result",
                variables=("B", "n"),
            ),
        ),
        (
            PRIME_LE_TWENTY_TWO_CASES,
            "omit_nineteen",
            cases_result,
            cases_without_19,
        ),
        (
            NONZERO_REMAINDER_NOT_MULTIPLE,
            "allow_zero_remainder",
            "~(r = 0)",
            "r = 0",
        ),
        (
            SCALED_REMAINDER_LIFT,
            "successor_tail",
            "c * x + r = d * (c * q + s) + u",
            "c * x + r = d * (c * q + s) + S u",
        ),
        (
            ADD_REMAINDER_LIFT,
            "successor_tail",
            "x + y = d * ((q + s) + u) + v",
            "x + y = d * ((q + s) + u) + S v",
        ),
        (
            DOUBLE_SCALED_REMAINDER_LIFT,
            "successor_tail",
            "2 * (11 * x) + 37 = d * (2 * (11 * q + s) + u) + v",
            "2 * (11 * x) + 37 = d * (2 * (11 * q + s) + u) + S v",
        ),
    ]
    for name, target, _number in _CERTIFICATES:
        tag = f"bb8cert_{name}"
        mutations.append(
            (
                name,
                "successor_is_composite",
                _prime(target, tag=tag, variables=()),
                _prime(f"S ({target})", tag=tag, variables=()),
            )
        )
    return tuple(mutations)


def test_b8_prime_certificate_mutations_have_counterfixtures() -> None:
    assert 2 == 2 * 1 and 2 != 1
    assert 6 == 2 * 3 and 6 < 3 * 3 and not 3 <= 2
    assert 4 % 2 == 0 and not 3 <= 2
    assert 3 < 3 * 3 and 4 == 2 * 2
    assert 19 not in (2, 3, 5, 7, 11, 13, 17)
    assert 4 == 2 * 2 + 0 and 4 % 2 == 0
    assert 0 != 1
    assert 37 == 1 * 37 and 37 != 38
    for _name, _target, number in _CERTIFICATES:
        successor = number + 1
        assert successor > 2 and successor % 2 == 0


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_b8_prime_certificate_genuine_mutations_are_rejected(
    name: str,
    case_id: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = _table(_specs())[name]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_b8_prime_certificate_independent_closures_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    formula, certificate = _close(name)
    assert formula == _closed_formula(item.statement)
    assert check((), certificate, formula)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        certificate,
        max_proof_occurrences=limits.max_candidate_proof_occurrences,
        max_proof_objects=limits.max_candidate_proof_objects,
        max_proof_depth=limits.max_candidate_proof_depth,
        max_annotation_occurrences=(
            limits.max_candidate_annotation_occurrences
        ),
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_candidate_envelope_depth,
        label=f"B8 certificate closure {name}",
    )
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual = (
        nodes,
        depth,
        objects,
        edges,
        reused,
        envelope[3],
        envelope[4],
        _proof_dag_sha256(certificate),
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(certificate))
    direct_cut_count = 0
    probe = certificate
    while type(probe) is Cut:
        direct_cut_count += 1
        probe = probe.body
    assert direct_cut_count == len(item.dependencies)
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)
    assert actual == EXPECTED_CLOSURES[name]
