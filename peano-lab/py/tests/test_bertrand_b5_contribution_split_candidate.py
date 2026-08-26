"""Fail-closed audit for contribution intervals and the B5 three-way split."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
import gc
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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import (
    alpha_enrollment_v11,
    bertrand_prime_contribution_candidate as contribution_module,
    bertrand_primorial_foundation_candidate as foundation_module,
    editions_v11,
    finite_fold_surface as fold_surface,
    finite_product_prefix_suffix_candidate as split_module,
    theorems as stable_module,
)
from peano_lab.library.bertrand_b5_contribution_split_candidate import (
    PRIME_CONTRIBUTION_INTERVAL_EXISTS,
    PRIME_CONTRIBUTION_INTERVAL_FUNCTIONAL,
    PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXTEND,
    PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXISTS,
    PRIME_CONTRIBUTION_INTERVAL_PREFIX_SHIFT,
    PRIME_CONTRIBUTION_INTERVAL_PREFIX_TRANSPORT_ENTRY,
    PRIME_CONTRIBUTION_PREFIX_INTERVAL_SPLIT,
    PRIME_CONTRIBUTION_PREFIX_RESTRICT_ADD,
    PRIME_CONTRIBUTION_PRODUCT_LENGTH_EQ_TRANSPORT,
    PRIME_CONTRIBUTION_THREE_RANGE_SPLIT,
    make_bertrand_b5_contribution_split_candidate_theorems,
)
from peano_lab.library import bertrand_b5_contribution_split_candidate as module
from peano_lab.library.bertrand_prime_contribution_candidate import (
    _prime_contribution_choice_term,
    _prime_contribution_prefix_term,
    _prime_contribution_product_term,
    make_bertrand_prime_contribution_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _lt_term,
    _render_term,
    _validated_context,
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


PREFIX_EXTEND = PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXTEND
PREFIX_EXISTS = PRIME_CONTRIBUTION_INTERVAL_PREFIX_EXISTS
PREFIX_TRANSPORT = PRIME_CONTRIBUTION_INTERVAL_PREFIX_TRANSPORT_ENTRY
INTERVAL_EXISTS = PRIME_CONTRIBUTION_INTERVAL_EXISTS
INTERVAL_FUNCTIONAL = PRIME_CONTRIBUTION_INTERVAL_FUNCTIONAL
PREFIX_SHIFT = PRIME_CONTRIBUTION_INTERVAL_PREFIX_SHIFT
PREFIX_RESTRICT = PRIME_CONTRIBUTION_PREFIX_RESTRICT_ADD
PREFIX_SPLIT = PRIME_CONTRIBUTION_PREFIX_INTERVAL_SPLIT
LENGTH_TRANSPORT = PRIME_CONTRIBUTION_PRODUCT_LENGTH_EQ_TRANSPORT
THREE_RANGE_SPLIT = PRIME_CONTRIBUTION_THREE_RANGE_SPLIT

EXPECTED_NAMES = (
    PREFIX_EXTEND,
    PREFIX_EXISTS,
    PREFIX_TRANSPORT,
    INTERVAL_EXISTS,
    INTERVAL_FUNCTIONAL,
    PREFIX_SHIFT,
    PREFIX_RESTRICT,
    PREFIX_SPLIT,
    LENGTH_TRANSPORT,
    THREE_RANGE_SPLIT,
)
EXPECTED_DEPENDENCIES = {
    PREFIX_EXTEND: (
        "prime_contribution_choice_exists",
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    PREFIX_EXISTS: (
        "add_eq_zero_right",
        "succ_ne_zero",
        PREFIX_EXTEND,
    ),
    PREFIX_TRANSPORT: (
        "beta_at_unique",
        "prime_contribution_choice_functional",
    ),
    INTERVAL_EXISTS: ("beta_product_exists", PREFIX_EXISTS),
    INTERVAL_FUNCTIONAL: (
        "beta_product_transport_prefix",
        "beta_product_functional",
        PREFIX_TRANSPORT,
    ),
    PREFIX_SHIFT: (
        "add_le_add_left",
        "beta_at_unique",
        "prime_contribution_choice_functional",
    ),
    PREFIX_RESTRICT: ("le_add_right", "lt_of_lt_of_le"),
    PREFIX_SPLIT: (
        "beta_product_prefix_suffix_split",
        PREFIX_EXISTS,
        PREFIX_SHIFT,
        PREFIX_RESTRICT,
    ),
    LENGTH_TRANSPORT: (),
    THREE_RANGE_SPLIT: (LENGTH_TRANSPORT, PREFIX_SPLIT),
}
EXPECTED_DIRECT_CUTS = dict(
    zip(EXPECTED_NAMES, (3, 3, 2, 2, 3, 3, 2, 4, 0, 2), strict=True)
)
assert sum(EXPECTED_DIRECT_CUTS.values()) == 24

SOURCE_PINS = {
    "theorems.py":
        "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "finite_fold_surface.py":
        "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30",
    "bertrand_primorial_foundation_candidate.py":
        "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98",
    "bertrand_prime_contribution_candidate.py":
        "fe7dae9ad7e788c1c861e870a1a69fc872498b06267f05b9c6200bf1d45eee33",
    "finite_product_prefix_suffix_candidate.py":
        "b0e98632b5668a688067ecdddebe0f906db00ebe84c267b395592d5797d27d9d",
    "alpha_enrollment_v11.py":
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093",
    "editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    "bertrand_b5_contribution_split_candidate.py":
        "a5b1e955cdd903adc6ada446fbcdb56d620a8e89372e3c3b71183ec22cfe1b7b",
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-contribution-split-tranche-rfc-v1.md"
)
RFC_SHA256 = "190c1d4616eef0debea1944385c8be0f7f3f0ac2f29c1254aa8b8729db534fd6"

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    PREFIX_EXTEND: (
        35584,
        "40d6eb29f7b1c2ad3f8cdaf41138f0b1dd890569c5ef1ca56873ee56a4e7a928",
        "50ad7396a59ee97435947b3e09b555581942b19e9459dcc24b4cbdde1a11a186",
        "8a1e9e19cddf41b94275fcaa085b7c3455c0a99c637e9d1abdbab3912a7f2bf2",
    ),
    PREFIX_EXISTS: (
        17652,
        "8159b5fd3397e408463ca39181380fa7d69d5bbda639f00f086770f3259d7ac2",
        "436f0e7508d9d4f37ff2ad3245931764975490d7ee81954b49789bea94467f81",
        "fdffdea114fb55cddb83e49be4505066186af5534379d18f226c94e23eae73f0",
    ),
    PREFIX_TRANSPORT: (
        34841,
        "62a71780a76baa87b73ecf75c8209a66ec63e1d79b6289f9f95c4557e1e287be",
        "32cdab7eeb4f52c6cd5d8c7f7958400d3b92ef9e9a891e71a81f1581eba14270",
        "18e8f9f3b0ce256e6c6cacda98c6e867859204e60916c4657b19d692d70ff648",
    ),
    INTERVAL_EXISTS: (
        21307,
        "669b048122f47bbd4820e3c9409c47b7dab5d0cb952fb960ecd8bf39b67a5fbe",
        "4056d4c44cd3074c66c033cbf94a175e6c8e609e030e553542015342bd6dda12",
        "1864db5bd4563cbe5dd3eae222a39061a2ee0b3a876f35a321003ccda3a623b2",
    ),
    INTERVAL_FUNCTIONAL: (
        49437,
        "55208972e1e9b7a0873a17ab3c59c12a58c5632926f33d0eede85385c3d5fd4c",
        "613d68bbc658d22d6dae82ce63d761eb31f93d366a67509fc5e8bce5b0a04539",
        "1ab87e6b477a421c0764da3f43438fa7a0f6437f3b06e12ff261164ba84306a6",
    ),
    PREFIX_SHIFT: (
        36481,
        "daa9cac5393213df9f1783a9742bd1c5bd2e2013407515d6733062d35fe0ac6c",
        "d885dc57d2a9ef5784bc75dd4fc8058cfa123f800356606cf42e12dc365d1fd7",
        "7f8c35215c5c323712284d452c1467a1110a1aabb2947ecad23d3a78521b11c3",
    ),
    PREFIX_RESTRICT: (
        35478,
        "55732e3620fb47f29cac9ed1620090add9e4a5b6f5173568078eff61757600c3",
        "d690343a1d3c717250fe59366a877edf6e607d3edd5ce8b4bc39e10b4f0f271a",
        "1598c321aedc8e535a86c087ba5b08c47f3bb598c11764dcbb27730addec9456",
    ),
    PREFIX_SPLIT: (
        67126,
        "4ab24ae4b359fc5abd62daadd6646cf709ffd0134135e03e86e808ca2134952b",
        "a612c09d7666d48664b8909fc0daf9969d83a037a37ac83a491ec1ad05706cd5",
        "03705e9832dc0c084b077b947dfe16114bfaa5d4a18eff11b479ac3f73b593aa",
    ),
    LENGTH_TRANSPORT: (
        45083,
        "4d768cb5ff8aadd78fcdc8fc8ae6bad4da5e4b393869e671e60c445f23cec871",
        "520d0ce712874b6459e6f887d1dd2823d6fb02f30bba3e7e1dcffd9bdfee1fe0",
        "4d768cb5ff8aadd78fcdc8fc8ae6bad4da5e4b393869e671e60c445f23cec871",
    ),
    THREE_RANGE_SPLIT: (
        87377,
        "92eb551d972a000823424b3e7ee72906ea4d05fe993d4ee2f48794346982bedf",
        "f52e00e12bfaf0e038e4f148d17c6f8ba1d373475f09c69cdded4fe7c0cdd9be",
        "16c60a9763f84e9c0e09d49406be58fd18b2f7d273b9e432850cb184d227d4f5",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    PREFIX_EXTEND: (3, 51, 90, 33, 90, 89, 0),
    PREFIX_EXISTS: (3, 22, 35, 17, 35, 34, 0),
    PREFIX_TRANSPORT: (2, 42, 77, 29, 77, 76, 0),
    INTERVAL_EXISTS: (2, 16, 23, 13, 23, 22, 0),
    INTERVAL_FUNCTIONAL: (3, 35, 65, 30, 65, 64, 0),
    PREFIX_SHIFT: (3, 53, 87, 30, 87, 86, 0),
    PREFIX_RESTRICT: (2, 17, 38, 23, 38, 37, 0),
    PREFIX_SPLIT: (4, 56, 76, 28, 76, 75, 0),
    LENGTH_TRANSPORT: (0, 11, 27, 15, 27, 26, 0),
    THREE_RANGE_SPLIT: (2, 64, 71, 25, 71, 70, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    PREFIX_EXTEND: (90, 90, 33, 8489, 66),
    PREFIX_EXISTS: (35, 35, 17, 728, 47),
    PREFIX_TRANSPORT: (77, 77, 29, 72, 29),
    INTERVAL_EXISTS: (23, 23, 13, 9, 13),
    INTERVAL_FUNCTIONAL: (65, 65, 30, 22, 30),
    PREFIX_SHIFT: (87, 87, 30, 92, 30),
    PREFIX_RESTRICT: (38, 38, 23, 8, 23),
    PREFIX_SPLIT: (76, 76, 28, 28, 28),
    LENGTH_TRANSPORT: (27, 27, 15, 3384, 56),
    THREE_RANGE_SPLIT: (71, 71, 25, 30, 25),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    PREFIX_EXTEND: (
        216804,
        95,
        6439,
        6723,
        285,
        729757,
        95,
        "da2d9c8324976755b3ae088bc564eda3515957adc76ebf1022d60a0a57db7eca",
    ),
    PREFIX_EXISTS: (
        216859,
        98,
        6474,
        6760,
        287,
        734120,
        98,
        "91cf764fa9de0169a693832d5e88ccf00b4e066c9be0e675106d14dd1e224e7a",
    ),
    PREFIX_TRANSPORT: (
        4256,
        67,
        1464,
        1507,
        44,
        22919,
        67,
        "d76294cb5f1ff31709d77ced55f506b7e5a45b1ac744db6af9f34cc295d97a0b",
    ),
    INTERVAL_EXISTS: (
        247369,
        100,
        6497,
        6784,
        288,
        835979,
        100,
        "fd5c8b652f6b4ef6366eb90a1e7adc97e5e0fd36d3a21c04eecbf09c33eefc63",
    ),
    INTERVAL_FUNCTIONAL: (
        5762,
        70,
        1529,
        1574,
        46,
        34946,
        70,
        "d058771484dc2bc25fa551101dbe82c52a72af5fe2a9e8243cefe2f464840b1c",
    ),
    PREFIX_SHIFT: (
        4401,
        68,
        1503,
        1548,
        46,
        24733,
        68,
        "66fb11136ce603da016c9f654890110e94ac707f7eb357d67169c0691a9e299d",
    ),
    PREFIX_RESTRICT: (
        198,
        23,
        187,
        197,
        11,
        3212,
        47,
        "879d201780ef1f6a2dea2f4f59be46b6c3644275630e46b5be33d9972006f7e7",
    ),
    PREFIX_SPLIT: (
        284171,
        100,
        7332,
        7647,
        316,
        986508,
        100,
        "7a0334f27a852a77b765e75c5c5398f474460de6ab476d2b0c5c40515dc3dbb9",
    ),
    LENGTH_TRANSPORT: (
        27,
        15,
        27,
        26,
        0,
        3384,
        56,
        "2ae93a1162da8b2606740f6ed0523a4b8963be2691f2855310ab5a81860c9220",
    ),
    THREE_RANGE_SPLIT: (
        284269,
        102,
        7430,
        7745,
        316,
        1001135,
        102,
        "3434eef2feb9a758df2c950a18bf7bbd45949e793dd20ddeb33e779cb7555df9",
    ),
}


def _interval_prefix(
    number: str,
    offset: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    number_term, offset_term, code_term, scale_term, length_term = tuple(
        _render_term(source, label=label, context=context)
        for source, label in (
            (number, "independent interval number"),
            (offset, "independent interval offset"),
            (code, "independent interval code"),
            (scale, "independent interval scale"),
            (length, "independent interval length"),
        )
    )
    index, value = _binders(tag, context, ("index", "value"))
    local = context + (index, value)
    bound = _lt_term(
        index,
        length_term,
        tag=f"{tag}_bound",
        avoid=local,
    )
    decoded = _beta_at_term(
        code_term,
        scale_term,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    choice = _prime_contribution_choice_term(
        number_term,
        f"{offset_term} + {index}",
        value,
        tag=f"{tag}_choice",
        variables=local,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _interval(
    number: str,
    offset: str,
    length: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    number_term, offset_term, length_term, value_term = tuple(
        _render_term(source, label=label, context=context)
        for source, label in (
            (number, "independent interval number"),
            (offset, "independent interval offset"),
            (length, "independent interval length"),
            (value, "independent interval value"),
        )
    )
    code, scale = _binders(tag, context, ("code", "scale"))
    local = context + (code, scale)
    prefix = _interval_prefix(
        number_term,
        offset_term,
        code,
        scale,
        length_term,
        tag=f"{tag}_prefix",
        variables=local,
    )
    product = fold_surface._product_relation_term(
        code,
        scale,
        length_term,
        value_term,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def _surface_parts() -> dict[str, str]:
    transport = ("n", "a", "b", "c", "d", "e", "l", "i", "p")
    three = ("n", "s", "q", "g", "h", "z")
    return {
        "extend_before": _interval_prefix(
            "n", "a", "b", "c", "l",
            tag="bpcifpe_before", variables=("n", "a", "b", "c", "l"),
        ),
        "extend_after": _interval_prefix(
            "n", "a", "d", "e", "S l",
            tag="bpcifpe_after",
            variables=("n", "a", "b", "c", "l", "d", "e"),
        ),
        "prefix_exists": _interval_prefix(
            "n", "a", "b", "c", "l",
            tag="bpcipx_result", variables=("n", "a", "l", "b", "c"),
        ),
        "transport_left": _interval_prefix(
            "n", "a", "b", "c", "l",
            tag="bpcipt_left", variables=transport,
        ),
        "transport_right": _interval_prefix(
            "n", "a", "d", "e", "l",
            tag="bpcipt_right", variables=transport,
        ),
        "transport_bound": _lt_term(
            "i", "l", tag="bpcipt_bound", avoid=transport
        ),
        "transport_source": _beta_at_term(
            "b", "c", "i", "p", tag="bpcipt_source", avoid=transport
        ),
        "transport_target": _beta_at_term(
            "d", "e", "i", "p", tag="bpcipt_target", avoid=transport
        ),
        "exists": _interval(
            "n", "a", "l", "z", tag="bpci_exists",
            variables=("n", "a", "l", "z"),
        ),
        "functional_left": _interval(
            "n", "a", "l", "x", tag="bpci_functional_left",
            variables=("n", "a", "l", "x", "y"),
        ),
        "functional_right": _interval(
            "n", "a", "l", "y", tag="bpci_functional_right",
            variables=("n", "a", "l", "x", "y"),
        ),
        "shift_source": _prime_contribution_prefix_term(
            "n", "b", "c", "a + l", tag="bpcips_source",
            variables=transport,
        ),
        "shift_interval": _interval_prefix(
            "n", "a", "d", "e", "l", tag="bpcips_interval",
            variables=transport,
        ),
        "shift_bound": _lt_term(
            "i", "l", tag="bpcips_bound", avoid=transport
        ),
        "shift_source_entry": _beta_at_term(
            "b", "c", "a + i", "p",
            tag="bpcips_source_entry", avoid=transport,
        ),
        "shift_target_entry": _beta_at_term(
            "d", "e", "i", "p", tag="bpcips_target_entry",
            avoid=transport,
        ),
        "restrict_source": _prime_contribution_prefix_term(
            "n", "b", "c", "a + l", tag="bpcpra_source",
            variables=("n", "a", "b", "c", "l"),
        ),
        "restrict_target": _prime_contribution_prefix_term(
            "n", "b", "c", "a", tag="bpcpra_target",
            variables=("n", "a", "b", "c", "l"),
        ),
        "split_source": _prime_contribution_product_term(
            "n", "a + l", "z", tag="bpcpis_source",
            variables=("n", "a", "l", "z"),
        ),
        "split_prefix": _prime_contribution_product_term(
            "n", "a", "x", tag="bpcpis_prefix",
            variables=("n", "a", "l", "z", "x", "y"),
        ),
        "split_interval": _interval(
            "n", "a", "l", "y", tag="bpcpis_interval",
            variables=("n", "a", "l", "z", "x", "y"),
        ),
        "length_source": _prime_contribution_product_term(
            "n", "l", "z", tag="bpcplet_source",
            variables=("n", "l", "m", "z"),
        ),
        "length_target": _prime_contribution_product_term(
            "n", "m", "z", tag="bpcplet_target",
            variables=("n", "l", "m", "z"),
        ),
        "three_source": _prime_contribution_product_term(
            "n", "n + n", "z", tag="bpctrs_source", variables=three,
        ),
        "three_small": _prime_contribution_product_term(
            "n", "s", "x", tag="bpctrs_small",
            variables=three + ("x", "y", "w"),
        ),
        "three_middle": _interval(
            "n", "s", "g", "y", tag="bpctrs_middle",
            variables=three + ("x", "y", "w"),
        ),
        "three_high": _interval(
            "n", "q", "h", "w", tag="bpctrs_high",
            variables=three + ("x", "y", "w"),
        ),
    }


def _expected_statements() -> dict[str, str]:
    part = _surface_parts()
    return {
        PREFIX_EXTEND: (
            "forall n a b c l. "
            f"({part['extend_before']}) -> exists d e. "
            f"({part['extend_after']})"
        ),
        PREFIX_EXISTS: (
            f"forall n a l. exists b c. ({part['prefix_exists']})"
        ),
        PREFIX_TRANSPORT: (
            "forall n a b c d e l. "
            f"({part['transport_left']}) -> ({part['transport_right']}) -> "
            f"forall i p. ({part['transport_bound']}) -> "
            f"({part['transport_source']}) -> ({part['transport_target']})"
        ),
        INTERVAL_EXISTS: f"forall n a l. exists z. ({part['exists']})",
        INTERVAL_FUNCTIONAL: (
            "forall n a l x y. "
            f"({part['functional_left']}) -> "
            f"({part['functional_right']}) -> x = y"
        ),
        PREFIX_SHIFT: (
            "forall n a b c d e l. "
            f"({part['shift_source']}) -> ({part['shift_interval']}) -> "
            f"forall i p. ({part['shift_bound']}) -> "
            f"({part['shift_source_entry']}) -> "
            f"({part['shift_target_entry']})"
        ),
        PREFIX_RESTRICT: (
            "forall n a b c l. "
            f"({part['restrict_source']}) -> ({part['restrict_target']})"
        ),
        PREFIX_SPLIT: (
            "forall n a l z. "
            f"({part['split_source']}) -> (exists x y. "
            f"({part['split_prefix']}) /\\ "
            f"(({part['split_interval']}) /\\ z = x * y))"
        ),
        LENGTH_TRANSPORT: (
            "forall n l m z. l = m -> "
            f"({part['length_source']}) -> ({part['length_target']})"
        ),
        THREE_RANGE_SPLIT: (
            "forall n s q g h z. s + g = q -> q + h = n + n -> "
            f"({part['three_source']}) -> (exists x y w. "
            f"({part['three_small']}) /\\ (({part['three_middle']}) /\\ "
            f"(({part['three_high']}) /\\ z = (x * y) * w)))"
        ),
    }


@lru_cache(maxsize=1)
def _contribution_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_prime_contribution_candidate_theorems(TheoremSpec)[:2]


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_b5_contribution_split_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    alpha = {
        row.name: row for row in editions_v11.ALPHA_SPECS
        if row.name not in stable
    }
    contribution = _table(_contribution_specs())
    assert not set(EXPECTED_NAMES) & (set(stable) | set(alpha))
    assert not set(contribution) & set(stable)
    return stable | alpha | contribution


def _row_core(name: str) -> dict[str, TheoremSpec]:
    return _core() | _table(_specs()[: EXPECTED_NAMES.index(name)])


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    formula = _closed_formula(item.statement)
    target = formula
    available = _available()
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


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    stable = _specs_by_name()
    if name in stable:
        checked = replay(name)
        return checked.formula, checked.certificate
    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    for dependency_formula, dependency_proof in reversed(
        tuple(_close(dependency) for dependency in item.dependencies)
    ):
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    return formula, body


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
                (child, False) for child in children
                if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof)
                else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


@pytest.fixture
def _closure_cache_guard():
    """Release each large recursive proof DAG before the next root."""

    yield
    _close.cache_clear()
    gc.collect()


def test_bertrand_b5_contribution_split_sources_are_pinned() -> None:
    providers = (
        stable_module,
        fold_surface,
        foundation_module,
        contribution_module,
        split_module,
        alpha_enrollment_v11,
        editions_v11,
        module,
    )
    for provider in providers:
        path = Path(provider.__file__)
        assert sha256(path.read_bytes()).hexdigest() == SOURCE_PINS[path.name]
    root = Path(__file__).resolve().parents[3]
    rfc = root / RFC_PATH
    assert sha256(rfc.read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_b5_contribution_split_factory_is_exact() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert tuple(row.statement for row in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {row.name: row.dependencies for row in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_b5_contribution_split_candidate_theorems"
    ]
    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v11.ALPHA_ENTRIES}
    assert not set(EXPECTED_NAMES) & stable
    assert not set(EXPECTED_NAMES) & alpha
    for index, name in enumerate(EXPECTED_NAMES):
        assert set(_row_core(name)) == set(_core()) | set(
            EXPECTED_NAMES[:index]
        )
    for row in rows:
        assert all(dep in _row_core(row.name) for dep in row.dependencies)
        parsed, free_names = parse_formula_with_names(row.statement)
        assert not free_names
        assert parsed == _closed_formula(row.statement)
        for token in (
            "ContributionInterval(",
            "ContributionProduct(",
            "Choice(",
            "Product(",
            "BetaAt(",
            "<=",
            "<",
            "^",
            "%",
            "|",
        ):
            assert token not in row.statement
        assert not any(
            bad in command
            for command in row.script
            for bad in (
                "DNE",
                "classical",
                "by_contra",
                "sorry",
                "auto",
                "compact_arith",
                "ring",
                "use ",
            )
        )
    provider_token = "bertrand_b5_contribution_split_candidate"
    for authority in (stable_module, alpha_enrollment_v11, editions_v11):
        assert provider_token not in Path(authority.__file__).read_text()


def test_bertrand_b5_contribution_split_topology_is_exact() -> None:
    table = _table(_specs())
    assert tuple(len(table[name].script) for name in EXPECTED_NAMES) == (
        51,
        22,
        42,
        16,
        35,
        53,
        17,
        56,
        11,
        64,
    )
    assert table[PREFIX_EXTEND].script.count("rewrite hsplit_left") == 12
    assert table[PREFIX_TRANSPORT].script.count("rewrite hpr") == 2
    assert table[PREFIX_SHIFT].script.count("rewrite hpr") == 2
    assert table[PREFIX_SPLIT].script.count(
        "apply beta_product_prefix_suffix_split"
    ) == 1
    assert table[LENGTH_TRANSPORT].script.count(
        "rewrite hlength at hsource"
    ) == 4
    final = table[THREE_RANGE_SPLIT].script
    assert final.count(
        "apply prime_contribution_prefix_interval_split"
    ) == 2
    assert final.count(
        "apply prime_contribution_product_length_eq_transport"
    ) == 2
    assert sum(command.startswith("rewrite") for command in final) == 1


def test_bertrand_b5_contribution_split_helpers_are_hygienic() -> None:
    variables = ("n", "a", "l", "m", "z")
    expected = _interval(
        "S n",
        "a + l",
        "S m",
        "z",
        tag="b5_split_hygiene",
        variables=variables,
    )
    actual = module._interval_relation_term(
        "S n",
        "a + l",
        "S m",
        "z",
        tag="b5_split_hygiene",
        variables=variables,
    )
    assert actual == expected
    parsed, free_names = parse_formula_with_names(actual)
    assert set(free_names) == set(variables)
    assert parsed == parse_formula_with_names(expected)[0]
    with pytest.raises(ValueError):
        module._interval_relation_term(
            "n", "a", "l", "z", tag="bad tag", variables=variables
        )
    with pytest.raises(ValueError):
        module._interval_relation_term(
            "n", "a", "l", "z", tag="valid", variables=[*variables]
        )
    with pytest.raises(ValueError):
        module._interval_relation_term(
            "n", "a", "l", "z", tag="valid",
            variables=("n", "a", "l", "z", "z"),
        )


def test_bertrand_b5_contribution_split_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_contribution_split_artifacts_are_frozen(
    name: str,
) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 CONTRIBUTION SPLIT {name} ARTIFACT actual={actual!r}")
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_contribution_split_bodies_are_frozen(name: str) -> None:
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
        label=f"B5 contribution split body {name}",
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
    assert not any(type(node) is DNE for node in _walk_proof(body))
    print(
        f"B5 CONTRIBUTION SPLIT {name} BODY actual={actual!r} "
        f"envelope={envelope!r}"
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == 24


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_b5_contribution_split_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(
            value for value in item.dependencies if value != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_contribution_split_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    changed = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    part = _surface_parts()
    same_code = _interval_prefix(
        "n", "a", "b", "c", "S l", tag="bpcifpe_after",
        variables=("n", "a", "b", "c", "l"),
    )
    shifted_transport = _beta_at_term(
        "d", "e", "i", "S p", tag="bpcipt_target",
        avoid=("n", "a", "b", "c", "d", "e", "l", "i", "p"),
    )
    shifted_entry = _beta_at_term(
        "d", "e", "i", "S p", tag="bpcips_target_entry",
        avoid=("n", "a", "b", "c", "d", "e", "l", "i", "p"),
    )
    longer_target = _prime_contribution_prefix_term(
        "n", "b", "c", "S a", tag="bpcpra_target",
        variables=("n", "a", "b", "c", "l"),
    )
    shifted_length_value = _prime_contribution_product_term(
        "n", "m", "S z", tag="bpcplet_target",
        variables=("n", "l", "m", "z"),
    )
    return (
        (
            PREFIX_EXTEND,
            "reuse_source_code",
            f"exists d e. ({part['extend_after']})",
            f"({same_code})",
        ),
        (
            PREFIX_EXISTS,
            "force_zero_code",
            f"exists b c. ({part['prefix_exists']})",
            f"exists b c. (({part['prefix_exists']}) /\\ b = 0)",
        ),
        (
            PREFIX_TRANSPORT,
            "shift_target_value",
            part["transport_target"],
            shifted_transport,
        ),
        (
            INTERVAL_EXISTS,
            "force_zero_value",
            f"exists z. ({part['exists']})",
            f"exists z. (({part['exists']}) /\\ z = 0)",
        ),
        (INTERVAL_FUNCTIONAL, "successor_result", "x = y", "x = S y"),
        (
            PREFIX_SHIFT,
            "shift_aligned_value",
            part["shift_target_entry"],
            shifted_entry,
        ),
        (
            PREFIX_RESTRICT,
            "extend_restricted_length",
            part["restrict_target"],
            longer_target,
        ),
        (PREFIX_SPLIT, "successor_product", "z = x * y", "z = S (x * y)"),
        (
            LENGTH_TRANSPORT,
            "shift_product_value",
            part["length_target"],
            shifted_length_value,
        ),
        (
            THREE_RANGE_SPLIT,
            "successor_total_product",
            "z = (x * y) * w",
            "z = S ((x * y) * w)",
        ),
    )


def test_bertrand_b5_contribution_split_mutations_have_fixtures() -> None:
    assert 0 != 2
    assert 1 != 0
    assert 2 != 3
    assert 1 != 2
    assert 1 != 2
    assert 2 != 3
    assert 1 != 2
    assert 1 != 2
    assert 1 != 2
    assert 1 != 2


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_bertrand_b5_contribution_split_mutations_are_rejected(
    name: str,
    case_id: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = _table(_specs())[name]
    assert item.statement.count(old) == 1
    changed = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_b5_contribution_split_closures_are_frozen(
    name: str,
    _closure_cache_guard,
) -> None:
    del _closure_cache_guard
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
        label=f"B5 contribution split closure {name}",
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    assert direct_cut_count == len(item.dependencies)
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)
    print(f"B5 CONTRIBUTION SPLIT {name} CLOSURE actual={actual!r}")
    assert EXPECTED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_CLOSURES[name]
