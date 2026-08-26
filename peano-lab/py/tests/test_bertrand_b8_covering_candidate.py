"""Fail-closed audit for the checked finite Bertrand covering chain."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero, parse_term_in_context, pretty_term
from peano_lab.library import (
    alpha_enrollment_v11,
    bertrand_b8_covering_candidate as module,
    bertrand_primorial_choose_interval_candidate,
    bertrand_primorial_foundation_candidate,
    bertrand_primorial_membership_candidate,
    editions_v11,
    theorems as stable_module,
)
from peano_lab.library.bertrand_b8_covering_candidate import (
    BERTRAND_ADD_SIX_PERMUTE,
    BERTRAND_ADD_SWAP_NESTED,
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
    BERTRAND_COVER_FIVE_SEVEN,
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
    BERTRAND_COVER_ONE_TWO,
    BERTRAND_COVER_SEVEN_THIRTEEN,
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
    BERTRAND_COVER_THREE_FIVE,
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
    BERTRAND_COVER_TWO_THREE,
    BERTRAND_COVERING_INTERVAL,
    make_bertrand_b8_covering_candidate_theorems,
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
    BERTRAND_ADD_SWAP_NESTED,
    BERTRAND_ADD_SIX_PERMUTE,
    BERTRAND_COVERING_INTERVAL,
    BERTRAND_COVER_ONE_TWO,
    BERTRAND_COVER_TWO_THREE,
    BERTRAND_COVER_THREE_FIVE,
    BERTRAND_COVER_FIVE_SEVEN,
    BERTRAND_COVER_SEVEN_THIRTEEN,
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
)

# The order remains largest-first for readable serial logs.  Proof-bearing
# tests also run each root in a fresh worker, so no interpreter retains more
# than one expanded proof DAG.
EXECUTION_NAMES = (
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
    BERTRAND_COVER_SEVEN_THIRTEEN,
    BERTRAND_COVER_FIVE_SEVEN,
    BERTRAND_COVER_THREE_FIVE,
    BERTRAND_COVER_TWO_THREE,
    BERTRAND_COVER_ONE_TWO,
    BERTRAND_COVERING_INTERVAL,
    BERTRAND_ADD_SIX_PERMUTE,
    BERTRAND_ADD_SWAP_NESTED,
)

EXPECTED_DEPENDENCIES = {
    BERTRAND_ADD_SWAP_NESTED: ("add_assoc", "add_comm"),
    BERTRAND_ADD_SIX_PERMUTE: (
        "add_assoc",
        BERTRAND_ADD_SWAP_NESTED,
    ),
    BERTRAND_COVERING_INTERVAL: (
        "add_le_add_right",
        "add_le_add_left",
        "le_trans",
    ),
    BERTRAND_COVER_ONE_TWO: (),
    BERTRAND_COVER_TWO_THREE: (),
    BERTRAND_COVER_THREE_FIVE: (),
    BERTRAND_COVER_FIVE_SEVEN: (),
    BERTRAND_COVER_SEVEN_THIRTEEN: (),
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE: (),
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE: (),
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE: (),
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE: (
        "add_mul",
        "add_assoc",
        "add_comm",
    ),
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN: (
        "add_mul",
        "mul_add",
        "add_assoc",
        "add_comm",
        BERTRAND_ADD_SWAP_NESTED,
        BERTRAND_ADD_SIX_PERMUTE,
    ),
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE: (
        "add_mul",
        "mul_add",
        "mul_assoc",
        "mul_comm",
        "add_assoc",
        "add_comm",
        "one_mul",
        BERTRAND_ADD_SIX_PERMUTE,
    ),
}

EXPECTED_DIRECT_CUTS = {
    name: len(EXPECTED_DEPENDENCIES[name]) for name in EXPECTED_NAMES
}

_COVERS = (
    (BERTRAND_COVER_ONE_TWO, "1", "2", "bb8c_one_two", 1, 2),
    (BERTRAND_COVER_TWO_THREE, "2", "3", "bb8c_two_three", 2, 3),
    (BERTRAND_COVER_THREE_FIVE, "3", "5", "bb8c_three_five", 3, 5),
    (BERTRAND_COVER_FIVE_SEVEN, "5", "7", "bb8c_five_seven", 5, 7),
    (
        BERTRAND_COVER_SEVEN_THIRTEEN,
        "7",
        "13",
        "bb8c_seven_thirteen",
        7,
        13,
    ),
    (
        BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
        "13",
        "23",
        "bb8c_thirteen_twenty_three",
        13,
        23,
    ),
    (
        BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
        "23",
        "43",
        "bb8c_twenty_three_forty_three",
        23,
        43,
    ),
    (
        BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
        "43",
        "9 * 9 + 2",
        "bb8c_forty_three_eighty_three",
        43,
        83,
    ),
    (
        BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
        "9 * 9 + 2",
        "13 * 12 + 7",
        "bb8c_eighty_three_one_sixty_three",
        83,
        163,
    ),
    (
        BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
        "13 * 12 + 7",
        "18 * 17 + 11",
        "bb8c_one_sixty_three_three_seventeen",
        163,
        317,
    ),
    (
        BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
        "18 * 17 + 11",
        "2 * (11 * 22) + 37",
        "bb8c_three_seventeen_five_twenty_one",
        317,
        521,
    ),
)

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
        "bertrand_b8_covering_candidate.py"
    ): "cd44578fee0cf4aa362f925d9f13bc8b64f511e4d3f628a40b5432e59b72b31e",
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
        "ha-bertrand-b8-covering-tranche-rfc-v1.md"
    ): "1c21f5eb30e7f34ac41013aa10da736f7604696829a907134c6b6b9e3e7720f5",
}


EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    BERTRAND_ADD_SWAP_NESTED: (
        39,
        "3e4f0e2202c60e8ecc760a871829c50f8abcd7a571f593126d1137fd0424a0e7",
        "f64ee3a2ba029cca9a6cb350b6062cc94d059b5528cb6b019d1856e51a8f616c",
        "d7860f53cd7d949956b021cd8f46985fa53184e6cb48ee2ef8164270c351be2f",
    ),
    BERTRAND_ADD_SIX_PERMUTE: (
        81,
        "3449070693e2107bff48730a73a851485bf284778b2f655246595419102df74f",
        "789ed73247e1125c7713d7726a4b022145b820983a20b90a0e7253627aa1fbcd",
        "7b276e489b2e80834c97c8c6d8e5a383adf9899724004ab4070846de2585bcd3",
    ),
    BERTRAND_COVERING_INTERVAL: (
        799,
        "513443d6c7017139980665bce7375bddfee58be02d3374080b192ac993eb4f64",
        "062c1c9d1690dc4dc12caf067d2bc54b7ace2130bb17b0691f7b2fec0c6aad6b",
        "3baff5d3e1a9753a88abf0ad0cd2e7ee502900fc5b1d2b5aefe47b82d13d9f06",
    ),
    BERTRAND_COVER_ONE_TWO: (
        71,
        "16174b8531edda852b19eeb694164fc3b15afb713bd019f9666e4d8fadc1d01f",
        "bfed236ac96c441221a098d49e8d24eafb30589d8db14c28549fb99cda45c7c5",
        "16174b8531edda852b19eeb694164fc3b15afb713bd019f9666e4d8fadc1d01f",
    ),
    BERTRAND_COVER_TWO_THREE: (
        75,
        "238deb166e783897f9b274b678cb7611acca37901b0ef593817990922438de2c",
        "9a2147d745434dab479f81ea3ed816a174088e8c7d0a33759bdff785143c70b2",
        "238deb166e783897f9b274b678cb7611acca37901b0ef593817990922438de2c",
    ),
    BERTRAND_COVER_THREE_FIVE: (
        77,
        "71012932afd25ed756e43e2acc31026e16a0fc43973cc615301e2697a6d990e6",
        "9a2147d745434dab479f81ea3ed816a174088e8c7d0a33759bdff785143c70b2",
        "71012932afd25ed756e43e2acc31026e16a0fc43973cc615301e2697a6d990e6",
    ),
    BERTRAND_COVER_FIVE_SEVEN: (
        77,
        "2b1165c4587b9b7a2991985895f5279d8ab166d21c740ffa0168a24968b11557",
        "f5f7a7858965f8e1ee324905341911c550a3b433713d73636df1f56de31cd2b9",
        "2b1165c4587b9b7a2991985895f5279d8ab166d21c740ffa0168a24968b11557",
    ),
    BERTRAND_COVER_SEVEN_THIRTEEN: (
        86,
        "b8ca6721d81b7e9ec30bd22c92337dd1a634bebc79cba3b3ffc6df04d9fb4163",
        "9a2147d745434dab479f81ea3ed816a174088e8c7d0a33759bdff785143c70b2",
        "b8ca6721d81b7e9ec30bd22c92337dd1a634bebc79cba3b3ffc6df04d9fb4163",
    ),
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE: (
        102,
        "ca484d4d8a2baff396c69d8655b8523ab5b0f0ea809d7b26299509de29f325d1",
        "f5f7a7858965f8e1ee324905341911c550a3b433713d73636df1f56de31cd2b9",
        "ca484d4d8a2baff396c69d8655b8523ab5b0f0ea809d7b26299509de29f325d1",
    ),
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE: (
        108,
        "9e3fdbf08b2de538d082d65c7922afab4a62225a12ad6a78a5ee119d09c43aa2",
        "f5f7a7858965f8e1ee324905341911c550a3b433713d73636df1f56de31cd2b9",
        "9e3fdbf08b2de538d082d65c7922afab4a62225a12ad6a78a5ee119d09c43aa2",
    ),
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE: (
        115,
        "4ab0eaca5b592681b20bf61e1760fd518e8c90ad2f33fb500035b12859e71b48",
        "f5f7a7858965f8e1ee324905341911c550a3b433713d73636df1f56de31cd2b9",
        "4ab0eaca5b592681b20bf61e1760fd518e8c90ad2f33fb500035b12859e71b48",
    ),
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE: (
        141,
        "807f5558eced949648a4633175679fa1fe87a1f215deb51f081544817476b5c7",
        "4074ea0962eeadaeb7549a14bb19c21bbac51ff79201fb77e195ca65139622a5",
        "3da101e4140d54d7a0175cf09527b8dcb87635a5194a93f24759ffd35d0cf4a5",
    ),
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN: (
        152,
        "c310f0c9a4a2da42afd6cf4de06e18d3651b4add205ef30ddd4f99ac676567a3",
        "c2dfdcc441b6e90ccdfb03f254a1cd35269e259792c0f7f9ef9a9839506fe334",
        "1a04f10bf604714c63a840fa96aa825d0aabd2dec72a172d6a5390a191f65ff3",
    ),
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE: (
        160,
        "062f4682aaac26a446c7730d8399ce8e07b60ade1cfb73f6855d9a429a4a0bda",
        "3f60acece2053412e1439425ddfb2df653798a2a635eeb7f58b902fff2e5b27a",
        "889b7c66bc01cc3ecd0ca1149179f4d43fda184ec153d90fac437c2326c99ea3",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    BERTRAND_ADD_SWAP_NESTED: (2, 11, 21, 11, 21, 20, 0),
    BERTRAND_ADD_SIX_PERMUTE: (2, 49, 78, 23, 78, 77, 0),
    BERTRAND_COVERING_INTERVAL: (3, 39, 40, 21, 40, 39, 0),
    BERTRAND_COVER_ONE_TWO: (0, 2, 36, 9, 36, 35, 0),
    BERTRAND_COVER_TWO_THREE: (0, 2, 50, 11, 50, 49, 0),
    BERTRAND_COVER_THREE_FIVE: (0, 2, 69, 15, 69, 68, 0),
    BERTRAND_COVER_FIVE_SEVEN: (0, 2, 97, 19, 97, 96, 0),
    BERTRAND_COVER_SEVEN_THIRTEEN: (0, 2, 145, 31, 145, 144, 0),
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE: (
        0, 2, 249, 51, 249, 248, 0,
    ),
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE: (
        0, 2, 439, 91, 439, 438, 0,
    ),
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE: (
        0, 2, 1262, 171, 1262, 1261, 0,
    ),
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE: (
        3, 40, 4578, 180, 4578, 4577, 0,
    ),
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN: (
        6, 67, 2222, 211, 2222, 2221, 0,
    ),
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE: (
        8, 162, 2939, 124, 2933, 2938, 6,
    ),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    BERTRAND_ADD_SWAP_NESTED: (21, 21, 11, 9, 11),
    BERTRAND_ADD_SIX_PERMUTE: (78, 78, 23, 81, 23),
    BERTRAND_COVERING_INTERVAL: (40, 40, 21, 23, 21),
    BERTRAND_COVER_ONE_TWO: (36, 36, 9, 19, 10),
    BERTRAND_COVER_TWO_THREE: (50, 50, 11, 37, 13),
    BERTRAND_COVER_THREE_FIVE: (69, 69, 15, 62, 16),
    BERTRAND_COVER_FIVE_SEVEN: (97, 97, 19, 130, 22),
    BERTRAND_COVER_SEVEN_THIRTEEN: (145, 145, 31, 232, 32),
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE: (249, 249, 51, 694, 54),
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE: (439, 439, 91, 2029, 94),
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE: (
        1262, 1262, 171, 11020, 174,
    ),
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE: (
        4578, 4578, 180, 39092, 182,
    ),
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN: (
        2222, 2222, 211, 20059, 220,
    ),
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE: (
        2939, 2933, 124, 18725, 124,
    ),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    BERTRAND_ADD_SWAP_NESTED: (
        127, 14, 116, 126, 11, 304, 16,
        "af3a500a8f8be0713940f1bd3f2535168391e9fa3f8b9f68f805e1015b9d6df3",
    ),
    BERTRAND_ADD_SIX_PERMUTE: (
        238, 23, 194, 205, 12, 554, 23,
        "bc36f0505a8254d0300a96ba4168c9ffcd0a653623a537a47fbb9019ee05cd9e",
    ),
    BERTRAND_COVERING_INTERVAL: (
        282, 21, 205, 217, 13, 946, 21,
        "70015da61d84e7278ac4ed6f203b51f0e88a4908d73b229eae1c7a1a59ca7c05",
    ),
    BERTRAND_COVER_ONE_TWO: (
        36, 9, 36, 35, 0, 19, 10,
        "4391c3b4d82fa42f3b5daeb3022420144d7926e3a0a7f21ba4b70deb31e5788c",
    ),
    BERTRAND_COVER_TWO_THREE: (
        50, 11, 50, 49, 0, 37, 13,
        "7576763f9014c3bdb61931e8868b6de03a72b236828cb37524688585fe409bb7",
    ),
    BERTRAND_COVER_THREE_FIVE: (
        69, 15, 69, 68, 0, 62, 16,
        "834cd14fe93c0f418b38cf60bed4c7f49d78be68db647d5ec65786457c925245",
    ),
    BERTRAND_COVER_FIVE_SEVEN: (
        97, 19, 97, 96, 0, 130, 22,
        "16e00a80660a8e7c6395bfe1a9167ed5fdda54420860e990691f6edaed8aff29",
    ),
    BERTRAND_COVER_SEVEN_THIRTEEN: (
        145, 31, 145, 144, 0, 232, 32,
        "3c638dc7806289f39311e10a8c6212169d0286b4f1c8f2a7cf1ae6bf933c9af6",
    ),
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE: (
        249, 51, 249, 248, 0, 694, 54,
        "07b19ae8d74c3e3db7807e5d97f5d8ffc867b23266677a822515a85f0a17d1b7",
    ),
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE: (
        439, 91, 439, 438, 0, 2029, 94,
        "b0aafe6b6e980362e088242b1f77896ef9e7cb50767fe4bcb25635ec07b5e322",
    ),
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE: (
        1262, 171, 1262, 1261, 0, 11020, 174,
        "acc68993bd09914aeccb0ba995a9cb5083a2f80f3cfdac6040bbbc9b5b28d0a6",
    ),
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE: (
        5010, 180, 4841, 4873, 33, 40561, 182,
        "2a3209dfd32af475ccba80486d953c52a2fcadb505c8e465f065a29fe199782f",
    ),
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN: (
        3096, 211, 2584, 2621, 38, 23191, 220,
        "9275e833fc21ba09fd89f85854dbf98c3581d6eb66e38641b0b3c105fffcaf99",
    ),
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE: (
        4050, 124, 3351, 3404, 54, 23243, 124,
        "e9245b7668e262e05b06f4fa395a15c7f04798929c145e000079d85ca0f0b3cf",
    ),
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


def _prime(value: str, *, tag: str, variables: tuple[str, ...]) -> str:
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


def _expected_statements() -> dict[str, str]:
    variables = ("a", "b", "n")
    result_variables = variables + ("p",)
    prime = _prime("b", tag="bb8ci_prime", variables=variables)
    lower = _le("a", "n", tag="bb8ci_lower", variables=variables)
    strict = _lt("n", "b", tag="bb8ci_strict", variables=variables)
    cover = _le("b", "a + a", tag="bb8ci_cover", variables=variables)
    result_prime = _prime(
        "p", tag="bb8ci_result_prime", variables=result_variables
    )
    result_strict = _lt(
        "n", "p", tag="bb8ci_result_strict", variables=result_variables
    )
    result_upper = _le(
        "p", "n + n", tag="bb8ci_result_upper", variables=result_variables
    )
    result = {
        BERTRAND_ADD_SWAP_NESTED: (
            "forall a b c. a + (b + c) = b + (a + c)"
        ),
        BERTRAND_ADD_SIX_PERMUTE: (
            "forall a b c d e f. ((a + b) + (c + d)) + (e + f) = "
            "(a + e) + ((b + c) + (d + f))"
        ),
        BERTRAND_COVERING_INTERVAL: (
            "forall a b n. "
            f"({prime}) -> ({lower}) -> ({strict}) -> ({cover}) -> "
            f"exists p. ({result_prime}) /\\ (({result_strict}) /\\ "
            f"({result_upper}))"
        ),
    }
    for name, left, right, tag, _left_value, _right_value in _COVERS:
        result[name] = _le(
            right,
            f"({left}) + ({left})",
            tag=tag,
            variables=(),
        )
    return result


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_b8_covering_candidate_theorems(TheoremSpec)
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


def _body_receipt(name: str) -> dict[str, object]:
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
        label=f"B8 covering body {name}",
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
    return {"body": list(actual), "envelope": list(envelope)}


def _closure_receipt(name: str) -> list[object]:
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
        label=f"B8 covering closure {name}",
    )
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual: list[object] = [
        nodes,
        depth,
        objects,
        edges,
        reused,
        envelope[3],
        envelope[4],
        _proof_dag_sha256(certificate),
    ]
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
    return actual


def _rejection_worker(
    kind: str,
    name: str,
    dependency: str | None,
) -> None:
    item = _table(_specs())[name]
    if kind == "dependency":
        assert dependency in item.dependencies
        changed = replace(
            item,
            dependencies=tuple(
                candidate
                for candidate in item.dependencies
                if candidate != dependency
            ),
        )
    elif kind == "false":
        assert dependency is None
        changed = replace(item, statement=f"({item.statement}) /\\ false")
    elif kind == "mutation":
        assert dependency is None
        matches = [case for case in _mutations() if case[0] == name]
        assert len(matches) == 1
        _name, _case_id, old, new = matches[0]
        assert item.statement.count(old) == 1
        changed = replace(
            item,
            statement=item.statement.replace(old, new, 1),
        )
    else:
        raise AssertionError(kind)
    try:
        replay_candidate_bodies((changed,), core=_row_core(name))
    except CandidateBodyError:
        return
    raise AssertionError(f"{kind} mutation unexpectedly replayed for {name}")


def _run_worker(arguments: list[str], prefix: str) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONMALLOC"] = "malloc"
    python_root = str(Path(__file__).resolve().parents[1])
    inherited_path = environment.get("PYTHONPATH")
    pieces = [python_root]
    if inherited_path:
        pieces.append(inherited_path)
    environment["PYTHONPATH"] = os.pathsep.join(pieces)
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *arguments],
        cwd=_repository_root(),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"isolated worker failed for {arguments!r}:\n"
        f"stdout={result.stdout[-4000:]}\n"
        f"stderr={result.stderr[-4000:]}"
    )
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(prefix)
    ]
    assert len(lines) == 1, result.stdout[-4000:]
    return json.loads(lines[0][len(prefix) :])


def _run_body_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--body-worker", name], "B8C_BODY ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_closure_worker(name: str) -> list[object]:
    payload = _run_worker(["--closure-worker", name], "B8C_CLOSURE ")
    assert payload["name"] == name
    receipt = payload["receipt"]
    assert isinstance(receipt, list)
    return receipt


def _run_rejection_worker(
    kind: str,
    name: str,
    dependency: str | None = None,
) -> None:
    arguments = ["--reject-worker", kind, name]
    if dependency is not None:
        arguments.append(dependency)
    payload = _run_worker(arguments, "B8C_REJECTION ")
    assert payload == {"kind": kind, "name": name}


def test_b8_covering_sources_and_contracts_are_pinned() -> None:
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
            "bertrand_b8_covering_candidate.py"
        ],
    }
    for provider, digest in providers.items():
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest
    root = _repository_root()
    for relative, digest in RFC_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest


def test_b8_covering_factory_is_exact_and_isolated() -> None:
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
    assert sum(EXPECTED_DIRECT_CUTS.values()) == 24
    assert tuple(EXPECTED_DIRECT_CUTS.values()) == (
        2, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 3, 6, 8,
    )
    for row in rows:
        assert row.statement == expected_statements[row.name]
        assert row.dependencies == EXPECTED_DEPENDENCIES[row.name]
        parsed, free_names = parse_formula_with_names(row.statement)
        assert isinstance(parsed, Formula)
        assert not free_names
        assert parsed == _closed_formula(row.statement)
    assert tuple(module.__all__) == (
        "BERTRAND_ADD_SWAP_NESTED",
        "BERTRAND_ADD_SIX_PERMUTE",
        "BERTRAND_COVERING_INTERVAL",
        "BERTRAND_COVER_ONE_TWO",
        "BERTRAND_COVER_TWO_THREE",
        "BERTRAND_COVER_THREE_FIVE",
        "BERTRAND_COVER_FIVE_SEVEN",
        "BERTRAND_COVER_SEVEN_THIRTEEN",
        "BERTRAND_COVER_THIRTEEN_TWENTY_THREE",
        "BERTRAND_COVER_TWENTY_THREE_FORTY_THREE",
        "BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE",
        "BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE",
        "BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN",
        "BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE",
        "make_bertrand_b8_covering_candidate_theorems",
    )

    provider_token = "bertrand_b8_covering_candidate"
    for authority_module in (stable_module, alpha_enrollment_v11, editions_v11):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source


def test_b8_covering_scripts_are_exact_and_constructive() -> None:
    rows = _table(_specs())
    expected_lengths = {
        BERTRAND_ADD_SWAP_NESTED: 11,
        BERTRAND_ADD_SIX_PERMUTE: 49,
        BERTRAND_COVERING_INTERVAL: 39,
        **{name: 2 for name, *_rest in _COVERS[:8]},
        BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE: 40,
        BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN: 67,
        BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE: 162,
    }
    forbidden = (
        "DNE", "by_contra", "classical", "compact_arith", "ring",
        "simp", "sorry", "use ", "induction ",
    )
    for name, row in rows.items():
        assert len(row.script) == expected_lengths[name]
        assert not any(
            token in command
            for command in row.script
            for token in forbidden
        )
    assert rows[BERTRAND_ADD_SIX_PERMUTE].script.count(
        f"apply {BERTRAND_ADD_SWAP_NESTED}"
    ) == 3
    assert rows[BERTRAND_COVERING_INTERVAL].script.count("apply le_trans") == 2
    assert rows[
        BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE
    ].script.count("norm_num") == 8


def test_b8_covering_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_b8_covering_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256("\0".join((item.statement, *item.dependencies)).encode()).hexdigest(),
    )
    print(f"B8 COVER {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_b8_covering_bodies_and_envelopes_are_frozen(name: str) -> None:
    receipt = _run_body_worker(name)
    actual = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(
        f"B8 COVER {name} BODY actual={actual!r} envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, (
        f"freeze body receipt for {name}: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[name] is not None, (
        f"freeze envelope receipt for {name}: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXECUTION_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == len(set(LIVE_EDGES)) == 24


@pytest.mark.parametrize(
    ("name", "dependency"),
    LIVE_EDGES,
    ids=tuple(f"{name}--{dependency}" for name, dependency in LIVE_EDGES),
)
def test_b8_covering_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    _run_rejection_worker("dependency", name, dependency)


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_b8_covering_false_targets_are_rejected(name: str) -> None:
    _run_rejection_worker("false", name)


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    expected = _expected_statements()
    variables = ("a", "b", "n", "p")
    old_upper = _le(
        "p", "n + n", tag="bb8ci_result_upper", variables=variables
    )
    new_upper = _le(
        "S p", "n + n", tag="bb8ci_result_upper", variables=variables
    )
    result = [
        (
            BERTRAND_ADD_SWAP_NESTED,
            "successor_result",
            "b + (a + c)",
            "S (b + (a + c))",
        ),
        (
            BERTRAND_ADD_SIX_PERMUTE,
            "successor_result",
            "(a + e) + ((b + c) + (d + f))",
            "S ((a + e) + ((b + c) + (d + f)))",
        ),
        (
            BERTRAND_COVERING_INTERVAL,
            "successor_upper_witness",
            old_upper,
            new_upper,
        ),
    ]
    for name, left, right, tag, _left_value, _right_value in _COVERS:
        old = expected[name]
        new = _le(right, left, tag=tag, variables=())
        result.append((name, "drop_doubling", old, new))
    return tuple(reversed(result))


def test_b8_covering_mutations_have_counterfixtures() -> None:
    assert 0 != 1
    assert not 3 <= 2
    for _name, _left, _right, _tag, left_value, right_value in _COVERS:
        assert right_value > left_value


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_b8_covering_genuine_mutations_are_rejected(
    name: str,
    case_id: str,
    old: str,
    new: str,
) -> None:
    del case_id, old, new
    _run_rejection_worker("mutation", name)


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_b8_covering_independent_closures_are_frozen(name: str) -> None:
    actual = tuple(_run_closure_worker(name))
    print(f"B8 COVER {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze independent closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]


def _main() -> None:
    assert len(sys.argv) >= 3
    mode = sys.argv[1]
    if mode == "--reject-worker":
        assert len(sys.argv) in (4, 5)
        kind = sys.argv[2]
        name = sys.argv[3]
        dependency = sys.argv[4] if len(sys.argv) == 5 else None
        assert name in EXPECTED_NAMES
        _rejection_worker(kind, name, dependency)
        print(
            "B8C_REJECTION "
            + json.dumps({"kind": kind, "name": name}, sort_keys=True),
            flush=True,
        )
        return

    assert len(sys.argv) == 3
    name = sys.argv[2]
    assert name in EXPECTED_NAMES
    if mode == "--body-worker":
        receipt: object = _body_receipt(name)
        prefix = "B8C_BODY "
    elif mode == "--closure-worker":
        receipt = _closure_receipt(name)
        prefix = "B8C_CLOSURE "
    else:
        raise AssertionError(mode)
    print(
        prefix
        + json.dumps({"name": name, "receipt": receipt}, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    _main()
