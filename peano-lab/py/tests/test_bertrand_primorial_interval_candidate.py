"""Fail-closed audit for offset Primorial intervals and prefix splitting."""

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
from peano_lab.kernel import terms as terms_module
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero, parse_term_in_context, pretty_term
from peano_lab.library import (
    alpha_enrollment_v9,
    bertrand_choose_foundation_candidate as choose_module,
    bertrand_primorial_foundation_candidate as foundation_module,
    bertrand_primorial_interval_candidate as module,
    editions_v9,
    finite_fold_surface as fold_surface,
    finite_product_prefix_suffix_candidate as split_module,
    theorems as stable_module,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    make_bertrand_primorial_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_interval_candidate import (
    make_bertrand_primorial_interval_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.finite_product_prefix_suffix_candidate import (
    make_finite_product_prefix_suffix_candidate_theorems,
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


PREFIX_EXTEND = "primorial_interval_factor_prefix_extend"
PREFIX_EXISTS = "primorial_interval_factor_prefix_exists"
PREFIX_TRANSPORT = "primorial_interval_factor_prefix_transport_entry"
INTERVAL_EXISTS = "primorial_interval_exists"
INTERVAL_FUNCTIONAL = "primorial_interval_functional"
PREFIX_SHIFT = "primorial_interval_factor_prefix_shift"
PREFIX_RESTRICT = "primorial_factor_prefix_restrict_add"
PRIMORIAL_SPLIT = "primorial_prefix_interval_split"

EXPECTED_NAMES = (
    PREFIX_EXTEND,
    PREFIX_EXISTS,
    PREFIX_TRANSPORT,
    INTERVAL_EXISTS,
    INTERVAL_FUNCTIONAL,
    PREFIX_SHIFT,
    PREFIX_RESTRICT,
    PRIMORIAL_SPLIT,
)
EXPECTED_DEPENDENCIES = {
    PREFIX_EXTEND: (
        "primorial_factor_choice_exists",
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
        "primorial_factor_choice_functional",
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
        "primorial_factor_choice_functional",
    ),
    PREFIX_RESTRICT: ("le_add_right", "lt_of_lt_of_le"),
    PRIMORIAL_SPLIT: (
        "beta_product_prefix_suffix_split",
        PREFIX_EXISTS,
        PREFIX_SHIFT,
        PREFIX_RESTRICT,
    ),
}
EXPECTED_DIRECT_CUTS = {
    name: count
    for name, count in zip(
        EXPECTED_NAMES,
        (3, 3, 2, 2, 3, 3, 2, 4),
        strict=True,
    )
}
assert sum(map(len, EXPECTED_DEPENDENCIES.values())) == 22

STABLE_SOURCE_SHA256 = (
    "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919"
)
FOLD_SOURCE_SHA256 = (
    "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30"
)
CHOOSE_SOURCE_SHA256 = (
    "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
)
TERMS_SOURCE_SHA256 = (
    "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185"
)
FOUNDATION_SOURCE_SHA256 = (
    "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98"
)
SPLIT_SOURCE_SHA256 = (
    "b0e98632b5668a688067ecdddebe0f906db00ebe84c267b395592d5797d27d9d"
)
SPLIT_TEST_SHA256 = (
    "86697086ff795fc1b3947e0470eba300f1c6e416e6f23b1c18dc2d5179ae5738"
)
ALPHA_ENROLLMENT_SOURCE_SHA256 = (
    "feebb3e5bbbcd58f6c6c7827650b4de4db0612839caad99120872b14d8c36087"
)
EDITIONS_SOURCE_SHA256 = (
    "68c2f6551827d9b1d09f2f49aa2b9dee430849aa06b4d2f2437ed8f1bb2775a5"
)
CANDIDATE_SOURCE_SHA256 = (
    "02e59e0f7addcae3bb127271ddeaa6728c5dab1dee096a878fced278065c10a3"
)
RFC_SHA256 = (
    "db7d2d58f0b44d3793673b21496ea7f5d5d2747c75795587f6b1c99b2e80f46e"
)

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    PREFIX_EXTEND: (
        2454,
        "2f29400592ec8ce27ab11627b8008c07ba3e0531380fea19b0090f33a59b297b",
        "5ffa6a3b254791e62b6b04aad5f43fd12e8f99da33ab0bc453a21c5914c0e617",
        "cbff25c805d2b4f72b31e0c56be95ecb0e282408187dcf0297609519ab3d4880",
    ),
    PREFIX_EXISTS: (
        1250,
        "f882fac9c2d2debea4c3165c1a4e86a654534a43e697c31711bdd246c2eecc54",
        "1f56249a879b9e529d2503f0714c29e390ad56d2259020cfe44d4bfd5a8b38f3",
        "a255c49cd637f0ff201c5bbf24ccb58e4a2a56236d6038acc392f5a7c91f4d6a",
    ),
    PREFIX_TRANSPORT: (
        2831,
        "676142406150430b74745b939ebcd4bf33a54199c848367cf4b5ffac1fc6efc5",
        "ea0dd053f5b9da0ff6828233d5b301d2007f4a643ac2a957c87b2b868d7fe56e",
        "60c037b163c5e46ca53688c28d0d887b542257a0ca062975df8d74f972a66f37",
    ),
    INTERVAL_EXISTS: (
        3425,
        "c01ebaa32f7cd58e26e924d409530dd3730bebbaed3a56584f09a39d53168c4c",
        "e32c3d173ee25487cd72e124fa2a46a34f13a85a3db5c5b9fb9e6752d6fe7250",
        "52f5e672b49a71672002a4ec5a2271cbd936d4212429919b0d642a0dfd91f5c9",
    ),
    INTERVAL_FUNCTIONAL: (
        8659,
        "aa7852889797a7513bd5505bbc843e1e2df8f555c943c44b798e92b7d714d3ec",
        "345a30cdc724b5a26df86bd477d06d51f1c39b4904ebdbe35208d3d8dba9613c",
        "4dd9941b23e240f558cc9a10f775dd66172617b2c4e5115c45147786297dccf0",
    ),
    PREFIX_SHIFT: (
        3031,
        "8700877fb7ec1171650b818ebfd67029fa3911b0564328e168e8e26e1e4232d0",
        "e130c90872a76cbe4292c80777e33466d00a2991a4ff94e305ecd8eabd898a17",
        "514d5befb41c255c25f70531ae312903cc31a22543fd1e75a41815ceea250efb",
    ),
    PREFIX_RESTRICT: (
        2436,
        "5e5d14a45782a164bccd983776f5940f2aab65752dbfd9eb978e658c1018549d",
        "eb3aa927f246e5b43c4e3ee88320e1aae33d3c1e1cfe507731ef33bf736bc369",
        "f041fa5671211d67af5268e065033232369f834bc8da343a15aed1052f0cb8ce",
    ),
    PRIMORIAL_SPLIT: (
        11004,
        "acdd4f5ae73a50887a5903944a35e1ccf19d51cb4360766dc5e8598341d71c6e",
        "821818bcf7e1e4a2e594450295027023e03dc89230135aadf32fc4d51deccc99",
        "a1b23201da46389a6ec142cab6fd12eb544674dcf8f08bb6dcb6d5b4440a9c60",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    PREFIX_EXTEND: (3, 43, 73, 27, 73, 72, 0),
    PREFIX_EXISTS: (3, 21, 33, 16, 33, 32, 0),
    PREFIX_TRANSPORT: (2, 37, 74, 28, 74, 73, 0),
    INTERVAL_EXISTS: (2, 15, 21, 12, 21, 20, 0),
    INTERVAL_FUNCTIONAL: (3, 33, 63, 29, 63, 62, 0),
    PREFIX_SHIFT: (3, 48, 84, 29, 84, 83, 0),
    PREFIX_RESTRICT: (2, 16, 37, 22, 37, 36, 0),
    PRIMORIAL_SPLIT: (4, 54, 72, 26, 72, 71, 0),
}
EXPECTED_ENVELOPES: dict[
    str, tuple[int, int, int, int, int] | None
] = {
    PREFIX_EXTEND: (73, 73, 27, 723, 36),
    PREFIX_EXISTS: (33, 33, 16, 122, 22),
    PREFIX_TRANSPORT: (74, 74, 28, 70, 28),
    INTERVAL_EXISTS: (21, 21, 12, 8, 12),
    INTERVAL_FUNCTIONAL: (63, 63, 29, 21, 29),
    PREFIX_SHIFT: (84, 84, 29, 90, 29),
    PREFIX_RESTRICT: (37, 37, 22, 8, 22),
    PRIMORIAL_SPLIT: (72, 72, 26, 25, 26),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    PREFIX_EXTEND: (
        31470,
        82,
        5199,
        5449,
        251,
        101341,
        82,
        "eaa57882a3a705e6734c2d7a6ba890f3e7fcb8abdb713fc7a4c179f6654c6376",
    ),
    PREFIX_EXISTS: (
        31523,
        85,
        5232,
        5484,
        253,
        102069,
        85,
        "97a1aa8a21831012762187d91d7de23041d5cde1f2cf58e334e52ed6d4b09899",
    ),
    PREFIX_TRANSPORT: (
        1270,
        60,
        841,
        877,
        37,
        3633,
        60,
        "3d11b1b5193dc1d978924b8b953d85e840c31ae9c1bb36995699afe156d8d817",
    ),
    INTERVAL_EXISTS: (
        62031,
        87,
        5489,
        5753,
        265,
        202109,
        87,
        "a10c6e57ce42b0f38ee94484cfa8e4849a597e3ad5f83d91430d028b4871de82",
    ),
    INTERVAL_FUNCTIONAL: (
        2774,
        63,
        1180,
        1219,
        40,
        10815,
        63,
        "6f4c7be5ca63b8458e6d67baab86c22dd5d29e04d4096418b5c7e678e90d88d3",
    ),
    PREFIX_SHIFT: (
        1415,
        61,
        880,
        918,
        39,
        4266,
        61,
        "306f3d7e9491093b2ad06c881024cacdb02fc0fdb712212b2065ef1062f56c06",
    ),
    PREFIX_RESTRICT: (
        197,
        22,
        186,
        196,
        11,
        830,
        22,
        "744a54c2ef3630ccdabe73a8b9f7cebb9cd0fb7f5df7c220ea8c09d59dd5acd6",
    ),
    PRIMORIAL_SPLIT: (
        95844,
        88,
        6197,
        6484,
        288,
        321423,
        88,
        "23053662aec4dbe1f34df402678c7bb9f7e7c7407295b77af724c8107e874c5d",
    ),
}


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(ch.isalnum() or ch in "_'" for ch in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _context(variables: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(variables, tuple):
        raise ValueError("variables must be a tuple")
    checked = tuple(_identifier(item, "context variable") for item in variables)
    if len(set(checked)) != len(checked):
        raise ValueError("context variables must be distinct")
    return checked


def _render(source: str, context: tuple[str, ...]) -> str:
    return pretty_term(
        parse_term_in_context(source, list(context)),
        list(context),
    ).replace("·", "*")


def _binders(
    tag: str,
    avoid: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"bpr_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated binder captures an argument")
    return names


def _lt(left: str, right: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    (gap,) = _binders(tag, avoid, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _at(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, avoid, ("height", "quotient"))
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value}))"
    )


def _prime(value: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    left, right = _binders(tag, avoid, ("left", "right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def _choice_rendered(
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    selected = f"S ({index})"
    prime = _prime(selected, tag=f"{tag}_prime", avoid=avoid)
    return (
        f"((({prime}) /\\ {value} = {selected}) \\/ "
        f"(~({prime}) /\\ {value} = 1))"
    )


def _prefix_rendered(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("index", "value"))
    local = avoid + (index, value)
    bound = _lt(index, length, tag=f"{tag}_bound", avoid=local)
    decoded = _at(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    choice = _choice_rendered(
        index,
        value,
        tag=f"{tag}_choice",
        avoid=local,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _prefix(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    return _prefix_rendered(
        _render(code, context),
        _render(scale, context),
        _render(length, context),
        tag=tag,
        avoid=context,
    )


def _primorial(
    index: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_index = _render(index, context)
    rendered_value = _render(value, context)
    code, scale = _binders(tag, context, ("code", "scale"))
    local = context + (code, scale)
    prefix = _prefix_rendered(
        code,
        scale,
        rendered_index,
        tag=f"{tag}_mask",
        avoid=local,
    )
    product = fold_surface._product_relation_term(
        code,
        scale,
        rendered_index,
        rendered_value,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def _interval_prefix_rendered(
    offset: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, value = _binders(tag, avoid, ("index", "value"))
    local = avoid + (index, value)
    bound = _lt(index, length, tag=f"{tag}_bound", avoid=local)
    decoded = _at(
        code,
        scale,
        index,
        value,
        tag=f"{tag}_decoded",
        avoid=local,
    )
    choice = _choice_rendered(
        f"{offset} + {index}",
        value,
        tag=f"{tag}_choice",
        avoid=local,
    )
    return (
        f"forall {index}. ({bound}) -> exists {value}. "
        f"(({decoded}) /\\ ({choice}))"
    )


def _interval_prefix(
    offset: str,
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    return _interval_prefix_rendered(
        _render(offset, context),
        _render(code, context),
        _render(scale, context),
        _render(length, context),
        tag=tag,
        avoid=context,
    )


def _interval(
    offset: str,
    length: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_offset = _render(offset, context)
    rendered_length = _render(length, context)
    rendered_value = _render(value, context)
    code, scale = _binders(tag, context, ("code", "scale"))
    local = context + (code, scale)
    prefix = _interval_prefix_rendered(
        rendered_offset,
        code,
        scale,
        rendered_length,
        tag=f"{tag}_mask",
        avoid=local,
    )
    product = fold_surface._product_relation_term(
        code,
        scale,
        rendered_length,
        rendered_value,
        tag=f"{tag}_product",
        avoid=local,
    )
    return f"exists {code} {scale}. (({prefix}) /\\ ({product}))"


def _surface_parts() -> dict[str, str]:
    transport = ("a", "b", "c", "d", "e", "l", "i", "p")
    shift = ("a", "b", "c", "d", "e", "l", "i", "p")
    return {
        "extend_before": _interval_prefix(
            "a",
            "b",
            "c",
            "l",
            tag="bpifpe_before",
            variables=("a", "b", "c", "l"),
        ),
        "extend_after": _interval_prefix(
            "a",
            "d",
            "e",
            "S l",
            tag="bpifpe_after",
            variables=("a", "b", "c", "l", "d", "e"),
        ),
        "prefix_exists": _interval_prefix(
            "a",
            "b",
            "c",
            "l",
            tag="bpifpx_result",
            variables=("a", "l", "b", "c"),
        ),
        "transport_left": _interval_prefix(
            "a", "b", "c", "l", tag="bpifpt_left", variables=transport
        ),
        "transport_right": _interval_prefix(
            "a", "d", "e", "l", tag="bpifpt_right", variables=transport
        ),
        "transport_bound": _lt(
            "i", "l", tag="bpifpt_bound", avoid=transport
        ),
        "transport_source": _at(
            "b", "c", "i", "p", tag="bpifpt_source", avoid=transport
        ),
        "transport_target": _at(
            "d", "e", "i", "p", tag="bpifpt_target", avoid=transport
        ),
        "exists": _interval(
            "a", "l", "z", tag="bpi_exists", variables=("a", "l", "z")
        ),
        "functional_left": _interval(
            "a",
            "l",
            "x",
            tag="bpi_functional_left",
            variables=("a", "l", "x", "y"),
        ),
        "functional_right": _interval(
            "a",
            "l",
            "y",
            tag="bpi_functional_right",
            variables=("a", "l", "x", "y"),
        ),
        "shift_source": _prefix(
            "b", "c", "a + l", tag="bpifps_source", variables=shift
        ),
        "shift_interval": _interval_prefix(
            "a", "d", "e", "l", tag="bpifps_interval", variables=shift
        ),
        "shift_bound": _lt("i", "l", tag="bpifps_bound", avoid=shift),
        "shift_source_entry": _at(
            "b",
            "c",
            "a + i",
            "p",
            tag="bpifps_source_entry",
            avoid=shift,
        ),
        "shift_target_entry": _at(
            "d", "e", "i", "p", tag="bpifps_target_entry", avoid=shift
        ),
        "restrict_source": _prefix(
            "b",
            "c",
            "a + l",
            tag="bpfpra_source",
            variables=("a", "b", "c", "l"),
        ),
        "restrict_target": _prefix(
            "b",
            "c",
            "a",
            tag="bpfpra_target",
            variables=("a", "b", "c", "l"),
        ),
        "split_source": _primorial(
            "a + l",
            "z",
            tag="bppis_source",
            variables=("a", "l", "z"),
        ),
        "split_prefix": _primorial(
            "a",
            "x",
            tag="bppis_prefix",
            variables=("a", "l", "z", "x", "y"),
        ),
        "split_interval": _interval(
            "a",
            "l",
            "y",
            tag="bppis_interval",
            variables=("a", "l", "z", "x", "y"),
        ),
    }


def _expected_statements() -> dict[str, str]:
    part = _surface_parts()
    return {
        PREFIX_EXTEND: (
            "forall a b c l. "
            f"({part['extend_before']}) -> exists d e. "
            f"({part['extend_after']})"
        ),
        PREFIX_EXISTS: (
            f"forall a l. exists b c. ({part['prefix_exists']})"
        ),
        PREFIX_TRANSPORT: (
            "forall a b c d e l. "
            f"({part['transport_left']}) -> ({part['transport_right']}) -> "
            f"forall i p. ({part['transport_bound']}) -> "
            f"({part['transport_source']}) -> ({part['transport_target']})"
        ),
        INTERVAL_EXISTS: f"forall a l. exists z. ({part['exists']})",
        INTERVAL_FUNCTIONAL: (
            "forall a l x y. "
            f"({part['functional_left']}) -> "
            f"({part['functional_right']}) -> x = y"
        ),
        PREFIX_SHIFT: (
            "forall a b c d e l. "
            f"({part['shift_source']}) -> ({part['shift_interval']}) -> "
            f"forall i p. ({part['shift_bound']}) -> "
            f"({part['shift_source_entry']}) -> "
            f"({part['shift_target_entry']})"
        ),
        PREFIX_RESTRICT: (
            "forall a b c l. "
            f"({part['restrict_source']}) -> ({part['restrict_target']})"
        ),
        PRIMORIAL_SPLIT: (
            "forall a l z. "
            f"({part['split_source']}) -> (exists x y. "
            f"({part['split_prefix']}) /\\ "
            f"(({part['split_interval']}) /\\ z = x * y))"
        ),
    }


@lru_cache(maxsize=1)
def _foundation_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_foundation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _split_specs() -> tuple[TheoremSpec, ...]:
    return make_finite_product_prefix_suffix_candidate_theorems(TheoremSpec)[:1]


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_interval_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    assert not (set(EXPECTED_NAMES) & set(stable))
    return stable | _table(_foundation_specs()) | _table(_split_specs())


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
        if tactic == "use":
            raise AssertionError("Primorial interval delegated through use")
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
    dependencies = tuple(_close(name) for name in item.dependencies)
    for dependency_formula, dependency_proof in reversed(dependencies):
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


def test_bertrand_primorial_interval_sources_are_pinned() -> None:
    expected = (
        (stable_module, STABLE_SOURCE_SHA256),
        (fold_surface, FOLD_SOURCE_SHA256),
        (choose_module, CHOOSE_SOURCE_SHA256),
        (terms_module, TERMS_SOURCE_SHA256),
        (foundation_module, FOUNDATION_SOURCE_SHA256),
        (split_module, SPLIT_SOURCE_SHA256),
        (alpha_enrollment_v9, ALPHA_ENROLLMENT_SOURCE_SHA256),
        (editions_v9, EDITIONS_SOURCE_SHA256),
        (module, CANDIDATE_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest
    root = Path(__file__).resolve().parents[3]
    split_test = root / "peano-lab/py/tests/" \
        "test_finite_product_prefix_suffix_candidate.py"
    assert sha256(split_test.read_bytes()).hexdigest() == SPLIT_TEST_SHA256
    rfc = root / "research/arithmetic-library/" \
        "ha-bertrand-primorial-interval-split-tranche-rfc-v1.md"
    assert sha256(rfc.read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_primorial_interval_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_primorial_interval_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v9.ALPHA_ENTRIES}
    support = set(_core())
    foundation_names = {item.name for item in _foundation_specs()}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert "beta_product_prefix_suffix_split" in support
    assert "beta_product_prefix_suffix_concat" not in support
    for index, name in enumerate(EXPECTED_NAMES):
        assert set(_row_core(name)) == support | set(EXPECTED_NAMES[:index])
    assert foundation_names <= support
    assert all(
        dependency in _row_core(item.name)
        for item in rows
        for dependency in item.dependencies
    )

    provider_token = "bertrand_primorial_interval_candidate"
    for authority in (stable_module, alpha_enrollment_v9, editions_v9):
        source = Path(authority.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    for item in rows:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        for token in (
            "Primorial(",
            "IntervalPrefix(",
            "FactorPrefix(",
            "Sel(",
            "Product(",
            "Prime(",
            "BetaAt(",
            "<=",
            "<",
            "^",
            "%",
            "|",
        ):
            assert token not in item.statement
        for command in item.script:
            assert all(
                token not in command
                for token in (
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


def test_bertrand_primorial_interval_script_topology_is_exact() -> None:
    table = _table(_specs())
    assert tuple(len(table[name].script) for name in EXPECTED_NAMES) == (
        43,
        21,
        37,
        15,
        33,
        48,
        16,
        54,
    )
    extend = table[PREFIX_EXTEND].script
    assert extend.count("rewrite hsplit_left") == 7
    assert extend.count("apply beta_prefix_extend") == 1
    assert extend.count("apply finite_lt_succ_eq_or_lt") == 1
    assert table[PREFIX_EXISTS].script.count("induction l") == 1
    transport = table[PREFIX_TRANSPORT].script
    assert transport.count("rewrite hpr") == 2
    functional = table[INTERVAL_FUNCTIONAL].script
    assert functional.count(
        "apply primorial_interval_factor_prefix_transport_entry"
    ) == 1
    assert functional.count("apply beta_product_transport_prefix") == 1
    shift = table[PREFIX_SHIFT].script
    assert shift.count("apply add_le_add_left") == 1
    assert shift.count("apply PA4") == 1
    assert shift.count("rewrite hpr") == 2
    restrict = table[PREFIX_RESTRICT].script
    assert restrict.count("apply lt_of_lt_of_le") == 1
    split = table[PRIMORIAL_SPLIT].script
    assert split.count("apply beta_product_prefix_suffix_split") == 1
    assert not any("prefix_suffix_concat" in command for command in split)
    assert not any(
        "rewrite" in command and "hprimorial" in command
        for command in split
    )


def test_bertrand_primorial_interval_helpers_are_hygienic() -> None:
    expected = _interval(
        "S a",
        "l + m",
        "z",
        tag="interval_hygiene",
        variables=("a", "l", "m", "z"),
    )
    actual = module._primorial_interval_relation_term(
        "S a",
        "l + m",
        "z",
        tag="interval_hygiene",
        variables=("a", "l", "m", "z"),
    )
    assert actual == expected
    parsed, free_names = parse_formula_with_names(actual)
    assert set(free_names) == {"a", "l", "m", "z"}
    assert parsed == parse_formula_with_names(expected)[0]
    prefix = _interval_prefix(
        "a",
        "b",
        "c",
        "S l",
        tag="prefix_hygiene",
        variables=("a", "b", "c", "l"),
    )
    assert module._primorial_interval_factor_prefix_term(
        "a",
        "b",
        "c",
        "S l",
        tag="prefix_hygiene",
        variables=("a", "b", "c", "l"),
    ) == prefix
    with pytest.raises(ValueError):
        module._primorial_interval_relation_term(
            "a", "l", "z", tag="bad tag", variables=("a", "l", "z")
        )
    with pytest.raises(ValueError):
        module._primorial_interval_relation_term(
            "a", "l", "z", tag="valid", variables=["a", "l", "z"]
        )
    with pytest.raises(ValueError):
        module._primorial_interval_relation_term(
            "a", "l", "z", tag="valid", variables=("a", "a", "z")
        )
    with pytest.raises(ValueError):
        module._primorial_interval_relation_term(
            "a", "l", "z", tag="valid", variables=("l", "z")
        )
    with pytest.raises(ValueError):
        module._primorial_interval_relation_term(
            "bpr_code_valid",
            "l",
            "z",
            tag="valid",
            variables=("bpr_code_valid", "l", "z"),
        )


def test_bertrand_primorial_interval_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_interval_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"PRIMORIAL INTERVAL {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_interval_bodies_are_frozen(name: str) -> None:
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
        label=f"Primorial interval body {name}",
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
        f"PRIMORIAL INTERVAL {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
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
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == 22


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_primorial_interval_every_dependency_is_live(
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
def test_bertrand_primorial_interval_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    part = _surface_parts()
    same_code = _interval_prefix(
        "a",
        "b",
        "c",
        "S l",
        tag="bpifpe_after",
        variables=("a", "b", "c", "l"),
    )
    shifted_transport = _at(
        "d",
        "e",
        "i",
        "S p",
        tag="bpifpt_target",
        avoid=("a", "b", "c", "d", "e", "l", "i", "p"),
    )
    shifted_entry = _at(
        "d",
        "e",
        "i",
        "S p",
        tag="bpifps_target_entry",
        avoid=("a", "b", "c", "d", "e", "l", "i", "p"),
    )
    longer_target = _prefix(
        "b",
        "c",
        "S a",
        tag="bpfpra_target",
        variables=("a", "b", "c", "l"),
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
        (
            INTERVAL_FUNCTIONAL,
            "successor_result",
            "x = y",
            "x = S y",
        ),
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
        (
            PRIMORIAL_SPLIT,
            "successor_product",
            "z = x * y",
            "z = S (x * y)",
        ),
    )


def test_bertrand_primorial_interval_mutations_have_counterfixtures() -> None:
    assert 0 != 2  # Offset 1, length 1 selects the prime factor 2.
    assert 2 != 3  # Decoded values cannot be incremented during transport.
    assert 2 != 0  # The singleton offset-1 interval product is 2.
    assert 1 != 2  # Empty interval functionality has value 1, not S 1.
    assert 1 != 2  # A vacuous prefix need not encode one more entry.
    assert 1 != 2  # Empty-prefix split has 1 = 1*1, not its successor.


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_bertrand_primorial_interval_genuine_mutations_are_rejected(
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
def test_bertrand_primorial_interval_closures_are_frozen(name: str) -> None:
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
        label=f"Primorial interval closure {name}",
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

    print(f"PRIMORIAL INTERVAL {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze independent closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
