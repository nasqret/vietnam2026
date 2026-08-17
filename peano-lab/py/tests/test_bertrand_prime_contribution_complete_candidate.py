"""Fail-closed audit for complete Bertrand prime contributions.

Large proof roots run in fresh subprocesses with ``PYTHONMALLOC=malloc`` so
no test interpreter retains more than one expanded proof DAG.
"""

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
from peano_lab.kernel.formulas import Eq, Formula, Imp
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v11
from peano_lab.library.bertrand_b5_order_quotient_candidate import (
    _divrem_term,
    make_bertrand_b5_order_quotient_candidate_theorems,
)
from peano_lab.library.bertrand_ceil_sqrt_candidate import (
    floor_sqrt_relation,
)
from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_central_binom_carry_candidate import (
    make_bertrand_central_binom_carry_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_factor_ranges_candidate import (
    make_bertrand_central_binom_factor_ranges_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_prime_support_candidate import (
    _no_bertrand_closed_term,
)
from peano_lab.library.bertrand_central_binom_square_tail_candidate import (
    make_bertrand_central_binom_square_tail_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_valuation_candidate import (
    make_bertrand_central_binom_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_zero_range_candidate import (
    make_bertrand_central_binom_zero_range_candidate_theorems,
)
from peano_lab.library.bertrand_prime_contribution_candidate import (
    _divides_rendered,
    _le_rendered,
    _power_divides_rendered,
    _power_rendered,
    _power_valuation_rendered,
    _prime_contribution_choice_term,
    _prime_contribution_prefix_term,
    _prime_contribution_product_term,
    make_bertrand_prime_contribution_candidate_theorems,
)
from peano_lab.library.bertrand_prime_contribution_complete_candidate import (
    CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS,
    NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES,
    NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES,
    PRIME_CONTRIBUTION_COFACTOR_EQ_ONE,
    PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION,
    PRIME_CONTRIBUTION_COMPLETE_EXISTS,
    PRIME_CONTRIBUTION_PRODUCT_EQ,
    PRIME_CONTRIBUTION_REVERSE_DIVIDES,
    PRIME_CONTRIBUTION_SELECTED_ENTRY,
    PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES,
    make_bertrand_prime_contribution_complete_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _lt_term,
    _prime_term,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    compile_layered_replay,
    intern_layered_replay_bodies,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    PRIME_CONTRIBUTION_SELECTED_ENTRY,
    PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES,
    PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION,
    PRIME_CONTRIBUTION_COFACTOR_EQ_ONE,
    PRIME_CONTRIBUTION_REVERSE_DIVIDES,
    PRIME_CONTRIBUTION_PRODUCT_EQ,
    PRIME_CONTRIBUTION_COMPLETE_EXISTS,
    CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS,
    NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES,
    NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES,
)

EXPECTED_DEPENDENCIES = {
    PRIME_CONTRIBUTION_SELECTED_ENTRY: (
        "beta_factor_divides_product",
    ),
    PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES: (
        "mul_assoc",
        "multiple_mul_left",
        "power_divides_successor_of_cofactor",
    ),
    PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION: (
        "prime_is_succ_succ",
        "multiple_mul_left",
        PRIME_CONTRIBUTION_SELECTED_ENTRY,
        PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES,
        "power_valuation_successor_not_divides",
    ),
    PRIME_CONTRIBUTION_COFACTOR_EQ_ONE: (
        "eq_decidable",
        "prime_divisor_exists",
        PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION,
    ),
    PRIME_CONTRIBUTION_REVERSE_DIVIDES: (
        "mul_one",
        "prime_contribution_product_divides",
        PRIME_CONTRIBUTION_COFACTOR_EQ_ONE,
    ),
    PRIME_CONTRIBUTION_PRODUCT_EQ: (
        "multiple_antisymm",
        "prime_contribution_product_divides",
        PRIME_CONTRIBUTION_REVERSE_DIVIDES,
    ),
    PRIME_CONTRIBUTION_COMPLETE_EXISTS: (
        "prime_contribution_product_exists",
        PRIME_CONTRIBUTION_PRODUCT_EQ,
    ),
    CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS: (
        "central_binom_positive",
        "central_binom_prime_divisor_le_double",
        PRIME_CONTRIBUTION_COMPLETE_EXISTS,
    ),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES: (
        "no_bertrand_central_prime_contribution_ranges",
    ),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES: (
        "beta_at_unique",
        NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES,
    ),
}

EXPECTED_COMMAND_COUNTS = {
    PRIME_CONTRIBUTION_SELECTED_ENTRY: 41,
    PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES: 31,
    PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION: 70,
    PRIME_CONTRIBUTION_COFACTOR_EQ_ONE: 41,
    PRIME_CONTRIBUTION_REVERSE_DIVIDES: 31,
    PRIME_CONTRIBUTION_PRODUCT_EQ: 19,
    PRIME_CONTRIBUTION_COMPLETE_EXISTS: 21,
    CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS: 32,
    NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES: 37,
    NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES: 45,
}

EXPECTED_CUT_COUNTS = (1, 3, 5, 3, 3, 3, 2, 3, 1, 2)

EXPECTED_ARTIFACTS = {
    PRIME_CONTRIBUTION_SELECTED_ENTRY: (
        36516,
        "e47af94853303cd0f032468132a73199c2fa00bc6e5ca1a4dd9e71a4acd6a2df",
        "a68814f3985267704deeb2dc946b747e3beb2607a28225a7d75b1462a6044418",
        "b3748cbbb906ba6aff0a5503f6e6020d77e2f92ea0c7cb0218a788874a058bac",
    ),
    PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES: (
        6460,
        "a02951517d0ed0a28a5e9e347c0798b933d2e94d0611db03b19e2f6571539f71",
        "e612b8d1222289f6cc116ca211f062675d6a10a1576b9f933b24e7f695af7a6a",
        "628379b0ded2dd079cbd51579edb17ecc062eab69922421c15469438b390fce1",
    ),
    PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION: (
        23453,
        "c36ba9b4050e51f934a516a39914a20a558c392b1c9b598a60f42640cf9f4f37",
        "44a19416624ea23d880e5b7ba2de0fd8b49690345bdb5b6435f13347d2a8c71d",
        "ff0de79127021095b597214b2df46817c01492776f375259cac1e8ee129fb074",
    ),
    PRIME_CONTRIBUTION_COFACTOR_EQ_ONE: (
        23174,
        "f7c035e6dab23e74bf2d5696caa25bd81f6924ef9b01752393fb9e557c6329ae",
        "f4fc76def66bb576b575119a19b2076ce984e0ca12d2539734777622eec30d70",
        "a73d5f4b5f5e2c0c3c1e818ba6835a79a72cbc3ce817d789a9fa5604674154b2",
    ),
    PRIME_CONTRIBUTION_REVERSE_DIVIDES: (
        22866,
        "23e00a832e6ab4df496da5e13c3b59acc5669da68609abe4431c374919f331dd",
        "da2f4b0396d1dc898de7cacff89b48a1f59fa7b425658516052b51bd617a92d6",
        "098132eff59400841fb62bf2144a7326147f7a25c7cfc5ab6ad68674cb5e7291",
    ),
    PRIME_CONTRIBUTION_PRODUCT_EQ: (
        23159,
        "a4162b74731d87c33e621b5da0b37a1bc248120aa0b48627782a61338be206f5",
        "a9446e5ecbc62b12a26d6b05a02dfb36da9efcefbcb5e61f0bd4141bb2d9e300",
        "8fba7bc6038c33892ca065fe04c9ef98d2d70ec9f66c207bd97856af1c68afc9",
    ),
    PRIME_CONTRIBUTION_COMPLETE_EXISTS: (
        22792,
        "cd64c3485c9d53656d6384ecf26acaee9223e77b29347a280fedd5f105dce544",
        "3d06634c5e33877d80b6d66f76e11e43bb7cbe9101fa5f20bc39d3127cf2018c",
        "fd4268ce6c971427697dc9c4f8023f0bfe5453f4d9ff326741ed624627505634",
    ),
    CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS: (
        30827,
        "50779cbe914310409862fbb719b0708643eb78c6d95aadf06ae1c2ef0be9fe82",
        "511bd67413ea34b177f4cd7faa38c5703b109b03dd50842d4dd8f5aa2d34639e",
        "fb1b41aceed8da9fc8d7e36929478295b090e0c6573be1c40548275b4f471e4c",
    ),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES: (
        24058,
        "1b9b7d6082553a709aadc5d7f407961e2f7cd10711b3040f4d1f6613dbc9067e",
        "b5a20a571daaf48279f28e5bbab2d8443712f7e6f64aac10d2c6adfba05d79c1",
        "26ee0dd683d1e85b70676576bc673ae70846aed47427f9c312359a389650266d",
    ),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES: (
        27128,
        "9b70df1d0fbd446beabf2c474d0b288511a0b2d7679406bfedefd0b70f2f28e4",
        "9de35607487e52e0f7577d4fb8f0fc6b7e437ec4944c2d614fbb6c514fbf48f2",
        "fa02b0c6192ca6882e05782e065e7f30082d393145d0b7d1feacc80ea7c6c396",
    ),
}
EXPECTED_BODIES = {
    PRIME_CONTRIBUTION_SELECTED_ENTRY: (1, 41, 52, 27, 52, 51, 0),
    PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES:
        (3, 31, 40, 23, 40, 39, 0),
    PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION:
        (5, 70, 93, 31, 93, 92, 0),
    PRIME_CONTRIBUTION_COFACTOR_EQ_ONE: (3, 41, 53, 26, 53, 52, 0),
    PRIME_CONTRIBUTION_REVERSE_DIVIDES: (3, 31, 41, 25, 41, 40, 0),
    PRIME_CONTRIBUTION_PRODUCT_EQ: (3, 19, 30, 18, 30, 29, 0),
    PRIME_CONTRIBUTION_COMPLETE_EXISTS: (2, 21, 23, 16, 23, 22, 0),
    CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS:
        (3, 32, 38, 18, 38, 37, 0),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES:
        (1, 37, 93, 49, 93, 92, 0),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES:
        (2, 45, 84, 37, 84, 83, 0),
}
EXPECTED_ENVELOPES = {
    PRIME_CONTRIBUTION_SELECTED_ENTRY: (52, 52, 27, 9, 27),
    PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES: (40, 40, 23, 22, 23),
    PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION:
        (93, 93, 31, 136, 33),
    PRIME_CONTRIBUTION_COFACTOR_EQ_ONE: (53, 53, 26, 15, 26),
    PRIME_CONTRIBUTION_REVERSE_DIVIDES: (41, 41, 25, 16, 25),
    PRIME_CONTRIBUTION_PRODUCT_EQ: (30, 30, 18, 8, 18),
    PRIME_CONTRIBUTION_COMPLETE_EXISTS: (23, 23, 16, 6, 16),
    CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS:
        (38, 38, 18, 10, 18),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES:
        (93, 93, 49, 9, 49),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES:
        (84, 84, 37, 152, 37),
}
EXPECTED_LAYERED_CLOSURES = {
    PRIME_CONTRIBUTION_SELECTED_ENTRY: (
        3027,
        66,
        753,
        1006,
        254,
        15005,
        66,
        "4676a75ffd184093f293414e7fbc76a7e38d0fb7d2166567fad01b64f7a4b27d",
    ),
    PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES: (
        65720,
        91,
        3690,
        5072,
        1383,
        219805,
        91,
        "5759c436c2829f41f046dba3db6be5a16b40bf10aa44c8a9f09ce2ebb7ef8484",
    ),
    PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION: (
        73799,
        93,
        4440,
        6066,
        1627,
        257473,
        93,
        "397d02d65625928b1a79827959fbd3c3c471ce955f339b144c60fb42ebd7fab2",
    ),
    PRIME_CONTRIBUTION_COFACTOR_EQ_ONE: (
        76899,
        94,
        4860,
        6693,
        1834,
        266974,
        94,
        "f737ec1cb2ef58174bad0f3249e8cb6e3f2ea67bdf1ca757f106a84980b29dcb",
    ),
    PRIME_CONTRIBUTION_REVERSE_DIVIDES: (
        98518,
        95,
        5715,
        7800,
        2086,
        339320,
        95,
        "f523de4d7449b9893ec3ff38613ee0bbc96a475559ab810853b8f116efae5554",
    ),
    PRIME_CONTRIBUTION_PRODUCT_EQ: (
        99214,
        95,
        5787,
        7904,
        2118,
        342583,
        95,
        "546b6ab0d8e505a549fd92fa0799d9fc18444a13bf607ffd36d345b060754ab0",
    ),
    PRIME_CONTRIBUTION_COMPLETE_EXISTS: (
        163294,
        95,
        6303,
        8581,
        2279,
        564722,
        95,
        "0b5a9df665bcda9f8f2d22ec407e140ef5abf1b00b10d7fdf54c72128dad8176",
    ),
    CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS: (
        241903,
        95,
        9647,
        13013,
        3367,
        840701,
        95,
        "aa7e5a6f68776889337db8cad15c30b9adc5afe2a1eee7726dfba1b58a5217a7",
    ),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES: (
        287414,
        95,
        15400,
        20141,
        4742,
        1053975,
        95,
        "1feb54491bd55395c63c7823e8f0e2a427314c8a57c5e65a06cd480f08cde190",
    ),
    NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES: (
        287510,
        95,
        15451,
        20205,
        4755,
        1058571,
        95,
        "b3f39fa3428e4c8fc5f24670c301b8a0df90013b398dd3508f59798144f094af",
    ),
}

SOURCE_PINS = {
    "editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    "alpha_enrollment_v11.py":
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093",
    "bertrand_b5_order_quotient_candidate.py":
        "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e",
    "bertrand_central_binom_valuation_candidate.py":
        "76ab449e7ae0dc58d7c99743e7df39e59d5619b8801387cd40a8cb242e2b79e8",
    "bertrand_central_binom_carry_candidate.py":
        "a480ca001ad0837c2ae45315bd5520c666d5e716a34c72ec5f5fcc0d7601c0f0",
    "bertrand_central_binom_square_tail_candidate.py":
        "b07163c977af5bbbf4f84aaec3629c9c58c06e8acc7fed476134e980aec7a9ff",
    "bertrand_central_binom_zero_range_candidate.py":
        "8ad4f3c5b90832dddc28d94f2b82f21eb47e8bd1e3f059696bbfa6e2b5c11b4e",
    "bertrand_central_binom_factor_ranges_candidate.py":
        "d03e4f7fb9a0f8f4de8db3022eb867cc600f4ec4f1a3050e3d9e35432ab4a8ae",
    "bertrand_prime_contribution_candidate.py":
        "fe7dae9ad7e788c1c861e870a1a69fc872498b06267f05b9c6200bf1d45eee33",
    "bertrand_prime_contribution_complete_candidate.py":
        "7e07f6c8908170d4aa12a3d234efb7b3200bd40f854de577ef12485ddca2f67d",
}

RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-prime-contribution-completeness-tranche-rfc-v1.md"
)
RFC_SHA256 = "0ec8561f2ea191df4e2d26edb381d8f48fcbb6c071d6e9dbe2e697b52517687e"


SUPPORT_FACTORIES = (
    make_bertrand_b5_order_quotient_candidate_theorems,
    make_bertrand_central_binom_valuation_candidate_theorems,
    make_bertrand_central_binom_carry_candidate_theorems,
    make_bertrand_central_binom_square_tail_candidate_theorems,
    make_bertrand_central_binom_zero_range_candidate_theorems,
    make_bertrand_central_binom_factor_ranges_candidate_theorems,
    make_bertrand_prime_contribution_candidate_theorems,
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_prime_contribution_complete_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    result: dict[str, TheoremSpec] = {}
    for row in editions_v11.ALPHA_SPECS:
        if row.name in stable:
            assert stable[row.name] == row
            continue
        result[row.name] = row
    for factory in SUPPORT_FACTORIES:
        for row in factory(TheoremSpec):
            previous = result.get(row.name)
            if previous is not None:
                assert previous == row
            else:
                assert row.name not in stable
                result[row.name] = row
    assert not set(EXPECTED_NAMES) & set(result)
    return result


def _row_candidates(name: str) -> dict[str, TheoremSpec]:
    prefix = _rows()[: EXPECTED_NAMES.index(name) + 1]
    return _candidate_base() | _table(prefix)


def _row_core(name: str) -> dict[str, TheoremSpec]:
    prefix = _rows()[: EXPECTED_NAMES.index(name)]
    return dict(_specs_by_name()) | _candidate_base() | _table(prefix)


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _candidate_base() | _table(_rows())


def _support(
    number: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (prime,) = _binders(tag, avoid, ("support_prime",))
    local = avoid + (prime,)
    primality = _prime_term(prime, tag=f"{tag}_prime", avoid=local)
    divides = _divides_rendered(
        prime,
        number,
        tag=f"{tag}_divides",
        avoid=local,
    )
    bound = _le_rendered(
        prime,
        length,
        tag=f"{tag}_bound",
        avoid=local,
    )
    return f"forall {prime}. ({primality}) -> ({divides}) -> ({bound})"


def _range_result(
    *,
    number: str,
    root: str,
    quotient: str,
    index: str,
    value: str,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    small_prime = _le_rendered(
        f"S {index}",
        root,
        tag=f"{tag}_small_prime",
        avoid=avoid,
    )
    small_value = _le_rendered(
        value,
        f"{number} + {number}",
        tag=f"{tag}_small_value",
        avoid=avoid,
    )
    above = _lt_term(
        root,
        f"S {index}",
        tag=f"{tag}_above",
        avoid=avoid,
    )
    middle = _le_rendered(
        f"S {index}",
        quotient,
        tag=f"{tag}_middle",
        avoid=avoid,
    )
    return (
        f"((({small_prime}) /\\ ({small_value})) \\/ "
        f"((({above}) /\\ ({middle})) /\\ {value} = S {index})) "
        f"\\/ {value} = 1"
    )


@lru_cache(maxsize=1)
def _expected_statements() -> dict[str, str]:
    selected_variables = ("n", "m", "z", "i")
    selected_prime = _prime_term(
        "S i", tag="bpcse_prime", avoid=selected_variables
    )
    selected_bound = _le_rendered(
        "S i", "m", tag="bpcse_bound", avoid=selected_variables
    )
    selected_source = _prime_contribution_product_term(
        "n", "m", "z", tag="bpcse_source", variables=selected_variables
    )
    exponent, value = _binders(
        "bpcse_result",
        selected_variables,
        ("selected_exponent", "selected_value"),
    )
    selected_local = selected_variables + (exponent, value)
    selected_valuation = _power_valuation_rendered(
        "S i",
        "n",
        exponent,
        tag="bpcse_result_valuation",
        avoid=selected_local,
    )
    selected_power = _power_rendered(
        "S i",
        exponent,
        value,
        tag="bpcse_result_power",
        avoid=selected_local,
    )
    selected_divides = _divides_rendered(
        value,
        "z",
        tag="bpcse_result_divides",
        avoid=selected_local,
    )
    selected_result = (
        f"exists {exponent} {value}. (({selected_valuation}) /\\ "
        f"(({selected_power}) /\\ ({selected_divides})))"
    )

    successor_variables = ("p", "e", "a", "z", "q", "n")
    successor_power = _power_rendered(
        "p", "e", "a", tag="bpcssd_power", avoid=successor_variables
    )
    successor_factor = _divides_rendered(
        "a", "z", tag="bpcssd_factor", avoid=successor_variables
    )
    successor_prime = _divides_rendered(
        "p",
        "q",
        tag="bpcssd_prime_factor",
        avoid=successor_variables,
    )
    successor_result = _power_divides_rendered(
        "p", "S e", "n", tag="bpcssd_result", avoid=successor_variables
    )

    contradiction_variables = ("n", "m", "z", "q", "p")
    contradiction_support = _support(
        "n", "m", tag="bpccpc_support", avoid=contradiction_variables
    )
    contradiction_product = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpccpc_product",
        variables=contradiction_variables,
    )
    contradiction_prime = _prime_term(
        "p", tag="bpccpc_prime", avoid=contradiction_variables
    )
    contradiction_divides = _divides_rendered(
        "p", "q", tag="bpccpc_divides", avoid=contradiction_variables
    )

    cofactor_variables = ("n", "m", "z", "q")
    cofactor_support = _support(
        "n", "m", tag="bpcceo_support", avoid=cofactor_variables
    )
    cofactor_product = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpcceo_product",
        variables=cofactor_variables,
    )

    common_variables = ("n", "m", "z")
    reverse_support = _support(
        "n", "m", tag="bpcrd_support", avoid=common_variables
    )
    reverse_product = _prime_contribution_product_term(
        "n", "m", "z", tag="bpcrd_product", variables=common_variables
    )
    reverse_result = _divides_rendered(
        "n", "z", tag="bpcrd_result", avoid=common_variables
    )
    equality_support = _support(
        "n", "m", tag="bpcpeq_support", avoid=common_variables
    )
    equality_product = _prime_contribution_product_term(
        "n", "m", "z", tag="bpcpeq_product", variables=common_variables
    )

    complete_variables = ("n", "m")
    complete_support = _support(
        "n", "m", tag="bpcce_support", avoid=complete_variables
    )
    complete_product = _prime_contribution_product_term(
        "n",
        "m",
        "z",
        tag="bpcce_product",
        variables=complete_variables + ("z",),
    )

    central_variables = ("n", "C")
    central = _central_binom_relation_term(
        "n", "C", tag="bcbpcpe_central", variables=central_variables
    )
    central_product = _prime_contribution_product_term(
        "C",
        "n + n",
        "z",
        tag="bcbpcpe_product",
        variables=central_variables + ("z",),
    )

    range_variables = ("n", "s", "q", "r", "C", "i", "a")
    exclusion = _no_bertrand_closed_term(
        "n", tag="bnbccr_exclusion", variables=range_variables
    )
    positive = _lt_term(
        "2", "n", tag="bnbccr_positive", avoid=range_variables
    )
    floor = floor_sqrt_relation("n + n", "s", tag="bnbccr_floor")
    division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="bnbccr_division",
        variables=range_variables,
    )
    range_central = _central_binom_relation_term(
        "n", "C", tag="bnbccr_central", variables=range_variables
    )
    choice = _prime_contribution_choice_term(
        "C", "i", "a", tag="bnbccr_choice", variables=range_variables
    )
    choice_range = _range_result(
        number="n",
        root="s",
        quotient="q",
        index="i",
        value="a",
        tag="bnbccr",
        avoid=range_variables,
    )

    prefix_variables = ("n", "s", "q", "r", "C", "b", "c")
    prefix_exclusion = _no_bertrand_closed_term(
        "n", tag="bnbcpr_exclusion", variables=prefix_variables
    )
    prefix_positive = _lt_term(
        "2", "n", tag="bnbcpr_positive", avoid=prefix_variables
    )
    prefix_floor = floor_sqrt_relation(
        "n + n", "s", tag="bnbcpr_floor"
    )
    prefix_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="bnbcpr_division",
        variables=prefix_variables,
    )
    prefix_central = _central_binom_relation_term(
        "n", "C", tag="bnbcpr_central", variables=prefix_variables
    )
    prefix = _prime_contribution_prefix_term(
        "C",
        "b",
        "c",
        "n + n",
        tag="bnbcpr_source",
        variables=prefix_variables,
    )
    prefix_local = prefix_variables + ("i", "a")
    prefix_bound = _lt_term(
        "i", "n + n", tag="bnbcpr_bound", avoid=prefix_local
    )
    decoded = _beta_at_term(
        "b", "c", "i", "a", tag="bnbcpr_decoded", avoid=prefix_local
    )
    prefix_range = _range_result(
        number="n",
        root="s",
        quotient="q",
        index="i",
        value="a",
        tag="bnbcpr",
        avoid=prefix_local,
    )

    return {
        PRIME_CONTRIBUTION_SELECTED_ENTRY:
            "forall n m z i. "
            f"({selected_prime}) -> ({selected_bound}) -> "
            f"({selected_source}) -> ({selected_result})",
        PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES:
            "forall p e a z q n. "
            f"({successor_power}) -> ({successor_factor}) -> "
            f"({successor_prime}) -> n = z * q -> ({successor_result})",
        PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION:
            "forall n m z q p. ~(n = 0) -> "
            f"({contradiction_support}) -> ({contradiction_product}) -> "
            f"n = z * q -> ({contradiction_prime}) -> "
            f"({contradiction_divides}) -> false",
        PRIME_CONTRIBUTION_COFACTOR_EQ_ONE:
            "forall n m z q. ~(n = 0) -> "
            f"({cofactor_support}) -> ({cofactor_product}) -> "
            "n = z * q -> q = 1",
        PRIME_CONTRIBUTION_REVERSE_DIVIDES:
            "forall n m z. ~(n = 0) -> "
            f"({reverse_support}) -> ({reverse_product}) -> "
            f"({reverse_result})",
        PRIME_CONTRIBUTION_PRODUCT_EQ:
            "forall n m z. ~(n = 0) -> "
            f"({equality_support}) -> ({equality_product}) -> n = z",
        PRIME_CONTRIBUTION_COMPLETE_EXISTS:
            "forall n m. ~(n = 0) -> "
            f"({complete_support}) -> exists z. "
            f"({complete_product}) /\\ n = z",
        CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS:
            "forall n C. "
            f"({central}) -> exists z. ({central_product}) /\\ C = z",
        NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES:
            "forall n s q r C i a. "
            f"({exclusion}) -> ({positive}) -> ({floor}) -> "
            f"({division}) -> ({range_central}) -> ({choice}) -> "
            f"({choice_range})",
        NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES:
            "forall n s q r C b c. "
            f"({prefix_exclusion}) -> ({prefix_positive}) -> "
            f"({prefix_floor}) -> ({prefix_division}) -> "
            f"({prefix_central}) -> ({prefix}) -> forall i a. "
            f"({prefix_bound}) -> ({decoded}) -> ({prefix_range})",
    }


@lru_cache(maxsize=1)
def _mutations() -> dict[str, str]:
    expected = _expected_statements()

    selected_variables = ("n", "m", "z", "i")
    exponent, value = _binders(
        "bpcse_result",
        selected_variables,
        ("selected_exponent", "selected_value"),
    )
    selected_local = selected_variables + (exponent, value)
    old_selected_power = _power_rendered(
        "S i",
        exponent,
        value,
        tag="bpcse_result_power",
        avoid=selected_local,
    )
    new_selected_power = _power_rendered(
        "S i",
        f"S {exponent}",
        value,
        tag="bpcse_result_power",
        avoid=selected_local,
    )

    successor_variables = ("p", "e", "a", "z", "q", "n")
    old_successor = _power_divides_rendered(
        "p", "S e", "n", tag="bpcssd_result", avoid=successor_variables
    )
    new_successor = _power_divides_rendered(
        "p",
        "S (S e)",
        "n",
        tag="bpcssd_result",
        avoid=successor_variables,
    )

    contradiction_variables = ("n", "m", "z", "q", "p")
    old_prime = _prime_term(
        "p", tag="bpccpc_prime", avoid=contradiction_variables
    )

    reverse_variables = ("n", "m", "z")
    old_reverse = _divides_rendered(
        "n", "z", tag="bpcrd_result", avoid=reverse_variables
    )
    new_reverse = _divides_rendered(
        "S n", "z", tag="bpcrd_result", avoid=reverse_variables
    )

    range_variables = ("n", "s", "q", "r", "C", "i", "a")
    old_exclusion = _no_bertrand_closed_term(
        "n", tag="bnbccr_exclusion", variables=range_variables
    )
    prefix_variables = ("n", "s", "q", "r", "C", "b", "c")
    old_prefix_exclusion = _no_bertrand_closed_term(
        "n", tag="bnbcpr_exclusion", variables=prefix_variables
    )

    replacements = {
        PRIME_CONTRIBUTION_SELECTED_ENTRY:
            (old_selected_power, new_selected_power),
        PRIME_CONTRIBUTION_SELECTED_SUCCESSOR_DIVIDES:
            (old_successor, new_successor),
        PRIME_CONTRIBUTION_COFACTOR_PRIME_CONTRADICTION:
            (f"({old_prime})", "(p = p)"),
        PRIME_CONTRIBUTION_COFACTOR_EQ_ONE:
            ("q = 1", "q = 0"),
        PRIME_CONTRIBUTION_REVERSE_DIVIDES:
            (old_reverse, new_reverse),
        PRIME_CONTRIBUTION_PRODUCT_EQ:
            ("-> n = z", "-> n = S z"),
        PRIME_CONTRIBUTION_COMPLETE_EXISTS:
            ("/\\ n = z", "/\\ n = S z"),
        CENTRAL_BINOM_PRIME_CONTRIBUTION_PRODUCT_EXISTS:
            ("/\\ C = z", "/\\ C = S z"),
        NO_BERTRAND_CENTRAL_CONTRIBUTION_CHOICE_RANGES:
            (f"({old_exclusion})", "(n = n)"),
        NO_BERTRAND_CENTRAL_CONTRIBUTION_PREFIX_RANGES:
            (f"({old_prefix_exclusion})", "(n = n)"),
    }
    result: dict[str, str] = {}
    for name, (old, new) in replacements.items():
        assert old != new
        assert expected[name].count(old) == 1, name
        result[name] = expected[name].replace(old, new)
        assert _closed_formula(result[name]) != _closed_formula(expected[name])
    return result


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _available()
    target = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
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
            pending.extend((child, False) for child in children)
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _body_receipt(name: str) -> dict[str, object]:
    item = _table(_rows())[name]
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
        label=f"B5 contribution-complete body {name}",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual = (
        len(item.dependencies),
        len(item.script),
        nodes,
        depth,
        objects,
        edges,
        reused,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(body))
    return {"body": list(actual), "envelope": list(envelope)}


def _rejection_worker(
    kind: str,
    name: str,
    dependency: str | None = None,
) -> None:
    item = _table(_rows())[name]
    if kind == "dependency":
        assert dependency is not None
        changed = replace(
            item,
            dependencies=tuple(
                entry for entry in item.dependencies if entry != dependency
            ),
        )
        assert len(changed.dependencies) + 1 == len(item.dependencies)
    elif kind == "false":
        assert dependency is None
        changed = replace(item, statement=f"({item.statement}) /\\ false")
    elif kind == "mutation":
        assert dependency is None
        changed = replace(item, statement=_mutations()[name])
    else:
        raise AssertionError(kind)
    try:
        replay_candidate_bodies((changed,), core=_row_core(name))
    except CandidateBodyError:
        return
    raise AssertionError(f"{kind} replay unexpectedly passed for {name}")


def _mutate_layer_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_layer_cut(proof.body, index - 1))


def _blueprint(name: str):
    stable = _specs_by_name()
    candidates = _row_candidates(name)
    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(current: str) -> None:
        if current in stable:
            stable_names.add(current)
            return
        item = candidates.get(current)
        assert item is not None, current
        mark = marks.get(current, 0)
        assert mark != 1
        if mark == 2:
            return
        marks[current] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[current] = 2
        candidate_order.append(current)

    visit(name)
    names = tuple(sorted(stable_names)) + tuple(candidate_order)
    positions = {entry: index for index, entry in enumerate(names)}
    specs = {
        entry: stable[entry] if entry in stable else candidates[entry]
        for entry in names
    }
    targets = {
        entry: _closed_formula(specs[entry].statement) for entry in names
    }
    dependencies = {
        entry: ()
        if entry in stable
        else tuple(positions[item] for item in specs[entry].dependencies)
        for entry in names
    }
    topology = "\x1c".join(
        "\x1f".join(
            (
                str(positions[entry]),
                entry,
                "stable_atomic" if entry in stable else "candidate_body",
                specs[entry].statement,
                "\x1e".join(names[index] for index in dependencies[entry]),
            )
        )
        for entry in names
    )
    return (
        stable,
        candidates,
        names,
        positions,
        specs,
        targets,
        dependencies,
        sha256(topology.encode()).hexdigest(),
    )


def _dependency_curried_body(
    item: TheoremSpec,
    targets: dict[str, Formula],
) -> Proof:
    target = targets[item.name]
    for dependency in reversed(item.dependencies):
        target = Imp(targets[dependency], target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


def _layered_receipt(name: str) -> dict[str, object]:
    (
        stable,
        candidates,
        names,
        positions,
        specs,
        targets,
        dependencies,
        topology_sha256,
    ) = _blueprint(name)
    nodes: list[LayeredReplayNode] = []
    candidate_count = 0
    for entry in names:
        if entry in stable:
            theorem = replay(entry)
            assert theorem.spec == stable[entry]
            assert theorem.formula == targets[entry]
            body = theorem.certificate
        else:
            candidate_count += 1
            body = _dependency_curried_body(specs[entry], targets)
        nodes.append(
            LayeredReplayNode(
                node_id=positions[entry],
                target=targets[entry],
                dependencies=dependencies[entry],
                body=body,
            )
        )
    assert names[-1] == name
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    raw = LayeredReplayBundle(tuple(nodes), positions[name])
    interned = intern_layered_replay_bodies(raw, targets[name], limits=limits)
    assert type(interned) is LayeredReplayBundle
    target_by_id = {node.node_id: node.target for node in interned.nodes}
    for node in interned.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(target_by_id[dependency], body_target)
        assert check((), node.body, body_target)
        assert not any(type(item) is DNE for item in _walk(node.body))
    compiled = compile_layered_replay(interned, targets[name], limits=limits)
    assert type(compiled) is LayeredReplayCandidate
    assert check((), compiled.certificate, compiled.target)
    assert not any(type(item) is DNE for item in _walk(compiled.certificate))
    layer_cuts = 0
    probe = compiled.certificate
    while type(probe) is Cut:
        layer_cuts += 1
        probe = probe.body
    assert layer_cuts == len(compiled.layers)
    for index in range(layer_cuts):
        assert not check(
            (),
            _mutate_layer_cut(compiled.certificate, index),
            compiled.target,
        )
    assert compiled.proof_nodes <= limits.max_candidate_proof_occurrences
    assert compiled.proof_objects <= limits.max_candidate_proof_objects
    assert compiled.proof_depth <= limits.max_candidate_proof_depth
    assert compiled.proof_annotation_occurrences <= (
        limits.max_candidate_annotation_occurrences
    )
    assert compiled.proof_envelope_depth <= limits.max_candidate_envelope_depth
    return {
        "topology_sha256": topology_sha256,
        "node_count": len(names),
        "stable_catalog_count": len(stable),
        "reachable_stable_count": len(names) - candidate_count,
        "candidate_body_count": candidate_count,
        "dependency_edge_count": sum(map(len, dependencies.values())),
        "layer_sizes": list(map(len, compiled.layers)),
        "layer_cut_count": layer_cuts,
        "proof_nodes": compiled.proof_nodes,
        "proof_depth": compiled.proof_depth,
        "proof_objects": compiled.proof_objects,
        "proof_edges": compiled.proof_edges,
        "reused_objects": compiled.reused_objects,
        "annotation_occurrences": compiled.proof_annotation_occurrences,
        "envelope_depth": compiled.proof_envelope_depth,
        "package_formula_occurrences": compiled.package_formula_occurrences,
        "package_formula_depth": compiled.maximum_package_formula_depth,
        "proof_dag_sha256": _proof_dag_sha256(compiled.certificate),
    }


def _run_worker(arguments: list[str], prefix: str) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONMALLOC"] = "malloc"
    python_root = str(Path(__file__).resolve().parents[1])
    inherited_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        python_root
        if not inherited_path
        else python_root + os.pathsep + inherited_path
    )
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *arguments],
        cwd=Path(__file__).resolve().parents[3],
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
    payload = _run_worker(["--body-worker", name], "B5PCC_BODY ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_closure_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--closure-worker", name], "B5PCC_CLOSURE ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_rejection_worker(
    kind: str,
    name: str,
    dependency: str | None = None,
) -> None:
    arguments = ["--reject-worker", kind, name]
    if dependency is not None:
        arguments.append(dependency)
    payload = _run_worker(arguments, "B5PCC_REJECTION ")
    assert payload == {"kind": kind, "name": name}


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


def test_bertrand_prime_contribution_complete_static_contract() -> None:
    rows = _rows()
    assert tuple(row.statement for row in rows) == tuple(
        _expected_statements()[name] for name in EXPECTED_NAMES
    )
    assert tuple(row.dependencies for row in rows) == tuple(
        EXPECTED_DEPENDENCIES[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.script for row in rows))) == tuple(
        EXPECTED_COMMAND_COUNTS[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.dependencies for row in rows))) == (
        EXPECTED_CUT_COUNTS
    )
    assert len(LIVE_EDGES) == 26
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        row.name for row in editions_v11.ALPHA_SPECS
    }
    assert rows[0].script.count("apply beta_factor_divides_product") == 1
    assert rows[2].script.count("rewrite hshape_witness at hp") == 2
    assert rows[2].script.count("rewrite hshape_witness at hbound") == 1
    assert rows[2].script.count("rewrite hshape_witness at hprime") == 1
    assert "factor_nonzero_right" not in rows[3].dependencies
    assert rows[3].script.count("apply prime_divisor_exists") == 1
    assert rows[9].script.count("rewrite heq") == 3
    assert not any(
        command.startswith("dne") for row in rows for command in row.script
    )
    forbidden = ("at hproduct", "at hcentral", "at hprefix")
    assert not any(
        "rewrite" in command and any(token in command for token in forbidden)
        for row in rows
        for command in row.script
    )


def test_bertrand_prime_contribution_complete_source_and_rfc_pins() -> None:
    library = Path(editions_v11.__file__).resolve().parent
    for filename, expected in SOURCE_PINS.items():
        assert sha256((library / filename).read_bytes()).hexdigest() == expected
    root = Path(__file__).resolve().parents[3]
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_prime_contribution_complete_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_LAYERED_CLOSURES) == EXPECTED_NAMES
    assert all(value is not None for value in EXPECTED_ARTIFACTS.values())
    assert all(value is not None for value in EXPECTED_BODIES.values())
    assert all(value is not None for value in EXPECTED_ENVELOPES.values())
    assert all(
        value is not None for value in EXPECTED_LAYERED_CLOSURES.values()
    )
    for name in EXPECTED_NAMES:
        body = EXPECTED_BODIES[name]
        assert body is not None
        assert body[5] - (body[4] - 1) == body[6]
        closure = EXPECTED_LAYERED_CLOSURES[name]
        assert closure is not None
        assert closure[3] - (closure[2] - 1) == closure[4]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_complete_artifacts(name: str) -> None:
    item = _table(_rows())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 CONTRIBUTION COMPLETE {name} ARTIFACT {actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_complete_bodies(name: str) -> None:
    receipt = _run_body_worker(name)
    actual = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(
        f"B5 CONTRIBUTION COMPLETE {name} BODY {actual!r} {envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_prime_contribution_complete_dependency_live(
    name: str,
    dependency: str,
) -> None:
    _run_rejection_worker("dependency", name, dependency)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_complete_false_targets(name: str) -> None:
    _run_rejection_worker("false", name)


def test_bertrand_prime_contribution_complete_counterfixtures() -> None:
    assert 2 ** 1 == 2 and 2 ** 2 != 2
    assert 2 ** 2 != 2
    assert 1 != 0
    assert not (2 <= 1)
    assert 1 != 2
    assert not (7 <= 3)
    assert 7 != 1


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_complete_mutations(name: str) -> None:
    _run_rejection_worker("mutation", name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_prime_contribution_complete_closures(name: str) -> None:
    actual_dict = _run_closure_worker(name)
    actual = (
        actual_dict["proof_nodes"],
        actual_dict["proof_depth"],
        actual_dict["proof_objects"],
        actual_dict["proof_edges"],
        actual_dict["reused_objects"],
        actual_dict["annotation_occurrences"],
        actual_dict["envelope_depth"],
        actual_dict["proof_dag_sha256"],
    )
    print(f"B5 CONTRIBUTION COMPLETE {name} CLOSURE {actual!r}", flush=True)
    expected = EXPECTED_LAYERED_CLOSURES[name]
    assert expected is not None, actual
    assert actual == expected


def _main() -> None:
    assert len(sys.argv) >= 3
    mode = sys.argv[1]
    name = sys.argv[2] if mode != "--reject-worker" else sys.argv[3]
    assert name in EXPECTED_NAMES
    if mode == "--body-worker":
        assert len(sys.argv) == 3
        receipt = _body_receipt(name)
        prefix = "B5PCC_BODY "
    elif mode == "--closure-worker":
        assert len(sys.argv) == 3
        receipt = _layered_receipt(name)
        prefix = "B5PCC_CLOSURE "
    elif mode == "--reject-worker":
        assert len(sys.argv) in (4, 5)
        kind = sys.argv[2]
        dependency = sys.argv[4] if len(sys.argv) == 5 else None
        _rejection_worker(kind, name, dependency)
        print(
            "B5PCC_REJECTION "
            + json.dumps({"kind": kind, "name": name}, sort_keys=True),
            flush=True,
        )
        return
    else:
        raise AssertionError(mode)
    print(
        prefix
        + json.dumps({"name": name, "receipt": receipt}, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    _main()
