from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from math import comb
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
from peano_lab.kernel.formulas import Formula, Imp
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v10
from peano_lab.library.bertrand_central_binom_candidate import (
    make_bertrand_central_binom_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_prime_support_candidate import (
    make_bertrand_central_binom_prime_support_candidate_theorems,
)
from peano_lab.library.bertrand_choose_diagonal_candidate import (
    make_bertrand_choose_diagonal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_factorial_bridge_candidate import (
    make_bertrand_choose_factorial_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_choose_factorial_support_candidate import (
    make_bertrand_choose_factorial_support_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    make_bertrand_choose_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    make_bertrand_choose_laws_candidate_theorems,
)
from peano_lab.library.bertrand_choose_pascal_candidate import (
    make_bertrand_choose_pascal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_recurrence_candidate import (
    make_bertrand_choose_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_choose_row_functional_candidate import (
    make_bertrand_choose_row_functional_candidate_theorems,
)
from peano_lab.library.bertrand_choose_symmetry_candidate import (
    make_bertrand_choose_symmetry_candidate_theorems,
)
from peano_lab.library.bertrand_choose_table_row_functional_candidate import (
    make_bertrand_choose_table_row_functional_candidate_theorems,
)
from peano_lab.library.bertrand_choose_weighted_vertical_candidate import (
    make_bertrand_choose_weighted_vertical_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_valuation_bridge_candidate import (
    make_bertrand_legendre_valuation_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_power_divisibility_candidate import (
    make_bertrand_power_divisibility_candidate_theorems,
)
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.bertrand_power_valuation_candidate import (
    power_valuation,
    make_bertrand_power_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_power_valuation_laws_candidate import (
    make_bertrand_power_valuation_law_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_choose_interval_candidate import (
    _prime_relation_term,
    make_bertrand_primorial_choose_interval_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _binders,
    _lt_term,
    _render_term,
    _validated_context,
)
from peano_lab.library.bertrand_primorial_membership_candidate import (
    _divides_term,
    _le_term,
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
    "central_binom_prime_divisor_le_double",
    "no_bertrand_central_prime_divisor_le",
    "power_valuation_nonzero_exponent_divides_base",
    "prime_divisor_power_valuation_nonzero",
    "no_bertrand_central_prime_divisor_ranges",
)

EXPECTED_DEPENDENCIES = {
    EXPECTED_NAMES[0]: (
        "factorial_exists",
        "choose_factorial_bridge",
        "mul_comm",
        "multiple_trans",
        "factorial_prime_le_of_divides",
    ),
    EXPECTED_NAMES[1]: (
        "le_total",
        "le_eq_or_lt",
        "le_refl",
        EXPECTED_NAMES[0],
    ),
    EXPECTED_NAMES[2]: (
        "one_le_of_ne_zero",
        "power_valuation_power_divides",
        "power_divides_exponent_antitone",
        "pow_one",
    ),
    EXPECTED_NAMES[3]: (
        "pow_exists",
        "pow_one",
        "prime_power_divides_exponent_le_valuation",
        "le_zero",
    ),
    EXPECTED_NAMES[4]: (
        "le_total",
        "le_eq_or_lt",
        "le_refl",
        EXPECTED_NAMES[1],
    ),
}

EXPECTED_DIRECT_EDGES = dict(
    zip(EXPECTED_NAMES, (5, 4, 4, 4, 4), strict=True)
)
assert sum(map(len, EXPECTED_DEPENDENCIES.values())) == 21

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    EXPECTED_NAMES[0]: (
        7911,
        "64fc582f91767cdfdb9f27d6eec3a7cf369b5596924a7bfc4fc255abc7cbd97a",
        "c44ada453f166899d476c9aab6b487775ab9c76bac2af756b60952780c792834",
        "d6a38246f9669212fa810d7af826fa6f285158895333df24e29c1d834d0b76b5",
    ),
    EXPECTED_NAMES[1]: (
        8880,
        "2edf39ef2ec7fc7e249ac9a632943bde633057d376321b904463b74f44da6674",
        "dce59a8f12ed9e43f4b5aa10232b87985b58e9a804998303c03e6e04148fc2b9",
        "5b85ec39d560fd49b73b23a6034500a559f1340318a9f4f6b7f82b8ca09d3014",
    ),
    EXPECTED_NAMES[2]: (
        8903,
        "22a1f82a7ec4d135267f9db5347c627faa73621d5dd3471895a3f824640c22a3",
        "5d732cea7be3523b29e59501eb371930227a64b8e1dd3b9547100aaf02cd8775",
        "423431588314dd6ad796ed5aec67bdf7a72a59fadd5c09213eedf63697584b42",
    ),
    EXPECTED_NAMES[3]: (
        8924,
        "8000af01e004415d265e86042a506b3c8a0cea2554309eadd883a00b6295ebbe",
        "56397755c83bd23e77d0983d69f8a91283189368c8d9c1c2c42abc5a892cbd6e",
        "43aa9b94fba57295c9780f706e3004f5f52de526a99e2ee17e46a44a3f1ea54c",
    ),
    EXPECTED_NAMES[4]: (
        9226,
        "3a80055b23fd86ef565367303929b95d8b0ef6f60cfa7144b846e4f6c5917da6",
        "eda237b536d7fd0c00c186ba5ce50d2512c81625ce988d594ca320f964d5a99a",
        "04de7a9c6eb607d8b42956b65ee7949468c3a315b5ed5f1f492d79a668d480fa",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    EXPECTED_NAMES[0]: (5, 47, 56, 31, 56, 55, 0),
    EXPECTED_NAMES[1]: (4, 35, 45, 24, 45, 44, 0),
    EXPECTED_NAMES[2]: (4, 34, 39, 17, 39, 38, 0),
    EXPECTED_NAMES[3]: (4, 43, 50, 27, 50, 49, 0),
    EXPECTED_NAMES[4]: (4, 63, 71, 28, 71, 70, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    EXPECTED_NAMES[0]: (56, 56, 31, 31, 32),
    EXPECTED_NAMES[1]: (45, 45, 24, 15, 24),
    EXPECTED_NAMES[2]: (39, 39, 17, 21, 17),
    EXPECTED_NAMES[3]: (50, 50, 27, 31, 27),
    EXPECTED_NAMES[4]: (71, 71, 28, 25, 28),
}
EXPECTED_LAYERED_CLOSURES: dict[
    str,
    tuple[int, int, int, int, int, int, int, str, str] | None,
] = {
    EXPECTED_NAMES[0]: (
        109058,
        94,
        6696,
        9147,
        2452,
        369007,
        94,
        "4350e618f3bdc55d8b3fc6171a2346ed8d8a2b28089a55b2a6dd81d9675bda39",
        "f7d95f277a2491efd323cbeca096ba880e4d1694734d84213a278a2bdb0d6685",
    ),
    EXPECTED_NAMES[1]: (
        109286,
        94,
        6757,
        9223,
        2467,
        370695,
        94,
        "325ff444c394404181f999785bc72c783546a6faca8df617b2a2ea19fa0f1473",
        "26a301c3661b5e2db89c2a96887c2b15e8572aef636a445fbf0b491f1d34664e",
    ),
    EXPECTED_NAMES[2]: (
        70811,
        92,
        3853,
        5313,
        1461,
        243792,
        92,
        "cc50d3d98fc4cec8f3ca3cdd6ba3b24a50094a4163a52122b545ea204e81c279",
        "073a52bb3e89f988ad014a1627665b3502721657901069c0f1df632dc1e2ddd2",
    ),
    EXPECTED_NAMES[3]: (
        68641,
        93,
        3952,
        5417,
        1466,
        233500,
        93,
        "ffb38aa51dedc96bec3cae207eb94328b06467c125f17ca29dc9fa3539b3a745",
        "852c47d762fa438f514896fddd5ef6ce44eebb1cfd671a9c758e5b2a521044e6",
    ),
    EXPECTED_NAMES[4]: (
        109382,
        94,
        6820,
        9304,
        2485,
        372092,
        94,
        "4cdea4c579fe2aedff0e9d75b168dba4a8573b77da9823e5557870ae49bfb53e",
        "b236a23ee92dfc36400aaf52eb0625e577520874b9d2436e6bc123acf8b14e35",
    ),
}

SOURCE_PINS = {
    "bertrand_choose_foundation_candidate.py": (
        "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
    ),
    "bertrand_choose_row_functional_candidate.py": (
        "dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf"
    ),
    "bertrand_choose_table_row_functional_candidate.py": (
        "379319daec74ad2e6b89b0808f885b87f6cc1a3fab4908559511d26f51be35f5"
    ),
    "bertrand_choose_laws_candidate.py": (
        "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d"
    ),
    "bertrand_choose_diagonal_candidate.py": (
        "96044d1bf4e10dfffba3f9f7482c4fd9ff1f94fffbccac9fe45af32a32a691bc"
    ),
    "bertrand_choose_recurrence_candidate.py": (
        "8b4a65b18e6a97a89c3f714686f2c690afb49f82ab56ed9575e3f673f50093c5"
    ),
    "bertrand_choose_pascal_candidate.py": (
        "e96ee1d140beece2666b901dc7d671743b01386f110628b0957aeff01b9c26c3"
    ),
    "bertrand_choose_symmetry_candidate.py": (
        "9958068fc364ca4bd171e965283a7683d167dcd6650e7a8df13f0b27c1edb78a"
    ),
    "bertrand_choose_weighted_vertical_candidate.py": (
        "e8629d085ccb2d69acb179ce2bcede5612edf290a39dac175476574f9ce76bd1"
    ),
    "bertrand_choose_factorial_support_candidate.py": (
        "d9fbdfb0bf3885ac2d3245b40c680dc28ec3e838fad7fb69736a96ee2734cccc"
    ),
    "bertrand_choose_factorial_bridge_candidate.py": (
        "22c07f0192b7e3cf6e85cb4b71fe70ecd3146c1c23cf6962ce261b369be10e09"
    ),
    "bertrand_central_binom_candidate.py": (
        "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e"
    ),
    "bertrand_primorial_choose_interval_candidate.py": (
        "5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09"
    ),
    "bertrand_power_order_candidate.py": (
        "50b07e3b40b81966a37bc07cbb44b93498a86efa76aabcbb4af94b17c1eb17e6"
    ),
    "bertrand_power_growth_candidate.py": (
        "41584397a149b7af19891bdd7b0f6b6366f6412c4c636508921af85d7220bfab"
    ),
    "bertrand_power_valuation_candidate.py": (
        "e1d7177ba713425dd3545fa7de2d78dae73ce155e09fabcfe6cd46fcf562fd57"
    ),
    "bertrand_power_valuation_laws_candidate.py": (
        "7b95e4f2a16df3866cb3e01f17d1b455000706454a1a241948957c4548a0a17f"
    ),
    "bertrand_power_divisibility_candidate.py": (
        "d3b0f53bd9e7de7c77b1fe2e80cdbedf001b9ff4c6b02c6aaa7f0e5aa5953963"
    ),
    "bertrand_legendre_valuation_bridge_candidate.py": (
        "6af2e6ad82bc47120cbf6f9d6b5dace8a2f20a45968d3dad88c6003c4637c89d"
    ),
    "bertrand_central_binom_prime_support_candidate.py": (
        "d48ed42c0b5289b1565947bb43dbcbe8389eed9aa196766ff90567cfc7fec7ab"
    ),
}

RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-central-prime-support-tranche-rfc-v1.md"
)
RFC_SHA256 = (
    "709a4ad357529d7f41ec086db1fd27fc9e4277f1ed0680532a9cb20d1ad02de9"
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


def _dedupe(rows: tuple[TheoremSpec, ...]) -> tuple[TheoremSpec, ...]:
    result: list[TheoremSpec] = []
    seen: dict[str, TheoremSpec] = {}
    for row in rows:
        old = seen.get(row.name)
        if old is not None:
            assert old == row
            continue
        seen[row.name] = row
        result.append(row)
    return tuple(result)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_prime_support_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    rows = (
        *make_bertrand_choose_foundation_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_table_row_functional_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_laws_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_diagonal_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_recurrence_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_pascal_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_symmetry_candidate_theorems(TheoremSpec)[:1],
        *make_bertrand_choose_weighted_vertical_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_factorial_support_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_factorial_bridge_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_candidate_theorems(TheoremSpec)[:1],
        *make_bertrand_primorial_choose_interval_candidate_theorems(
            TheoremSpec
        )[:2],
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_law_candidate_theorems(TheoremSpec),
        *make_bertrand_power_divisibility_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_valuation_bridge_candidate_theorems(
            TheoremSpec
        ),
    )
    return _dedupe(rows)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    prior = _table(_prior_specs())
    assert not set(stable) & set(prior)
    assert not set(EXPECTED_NAMES) & set(stable)
    assert not set(EXPECTED_NAMES) & set(prior)
    return stable | prior


def _row_core(name: str) -> dict[str, TheoremSpec]:
    return _core() | _table(_specs()[: EXPECTED_NAMES.index(name)])


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    formula = _closed_formula(item.statement)
    target = formula
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(_available()[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        assert tactic != "use"
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


def _no_bertrand(
    variables: tuple[str, ...],
    *,
    tag: str,
    upper: str,
) -> str:
    context = _validated_context(variables)
    (candidate,) = _binders(tag, context, ("prime_candidate",))
    local = context + (candidate,)
    lower = _lt_term("n", candidate, tag=f"{tag}_lower", avoid=local)
    upper_bound = _le_term(
        candidate,
        upper,
        tag=f"{tag}_upper",
        variables=local,
    )
    primality = _prime_relation_term(
        candidate,
        tag=f"{tag}_prime",
        variables=local,
    )
    return (
        f"forall {candidate}. (({lower}) /\\ ({upper_bound})) -> "
        f"~({primality})"
    )


def _central(
    n: str,
    c: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _validated_context(variables)
    rendered = _render_term(n, label="central test index", context=context)
    return _choose_relation_term(
        f"{rendered} + {rendered}",
        rendered,
        c,
        tag=tag,
        variables=context,
    )


def _expected_statements() -> dict[str, str]:
    base_variables = ("n", "c", "p")
    prime0 = _prime_relation_term(
        "p", tag="bcpdl_prime", variables=base_variables
    )
    central0 = _central(
        "n", "c", tag="bcpdl_central", variables=base_variables
    )
    divides0 = _divides_term(
        "p", "c", tag="bcpdl_divides", variables=base_variables
    )
    result0 = _le_term(
        "p", "n + n", tag="bcpdl_result", variables=base_variables
    )

    exclusion1 = _no_bertrand(
        base_variables,
        tag="bnbcpdl_exclusion",
        upper="n + n",
    )
    prime1 = _prime_relation_term(
        "p", tag="bnbcpdl_prime", variables=base_variables
    )
    central1 = _central(
        "n", "c", tag="bnbcpdl_central", variables=base_variables
    )
    divides1 = _divides_term(
        "p", "c", tag="bnbcpdl_divides", variables=base_variables
    )
    result1 = _le_term(
        "p", "n", tag="bnbcpdl_result", variables=base_variables
    )

    valuation_variables = ("p", "c", "e")
    valuation2 = power_valuation("p", "c", "e", tag="bpvnedb_source")
    result2 = _divides_term(
        "p", "c", tag="bpvnedb_result", variables=valuation_variables
    )
    prime3 = _prime_relation_term(
        "p", tag="bpdvpn_prime", variables=valuation_variables
    )
    valuation3 = power_valuation("p", "c", "e", tag="bpdvpn_source")
    divides3 = _divides_term(
        "p", "c", tag="bpdvpn_divides", variables=valuation_variables
    )

    range_variables = ("n", "s", "q", "c", "p")
    exclusion4 = _no_bertrand(
        range_variables,
        tag="bnbcpdr_exclusion",
        upper="n + n",
    )
    prime4 = _prime_relation_term(
        "p", tag="bnbcpdr_prime", variables=range_variables
    )
    central4 = _central(
        "n", "c", tag="bnbcpdr_central", variables=range_variables
    )
    divides4 = _divides_term(
        "p", "c", tag="bnbcpdr_divides", variables=range_variables
    )
    small4 = _le_term(
        "p", "s", tag="bnbcpdr_small", variables=range_variables
    )
    above_small4 = _lt_term(
        "s", "p", tag="bnbcpdr_above_small", avoid=range_variables
    )
    middle4 = _le_term(
        "p", "q", tag="bnbcpdr_middle_bound", variables=range_variables
    )
    above_middle4 = _lt_term(
        "q", "p", tag="bnbcpdr_above_middle", avoid=range_variables
    )
    row4 = _le_term(
        "p", "n", tag="bnbcpdr_row_bound", variables=range_variables
    )
    return {
        EXPECTED_NAMES[0]: (
            "forall n c p. "
            f"({prime0}) -> ({central0}) -> ({divides0}) -> ({result0})"
        ),
        EXPECTED_NAMES[1]: (
            "forall n c p. "
            f"({exclusion1}) -> ({prime1}) -> ({central1}) -> "
            f"({divides1}) -> ({result1})"
        ),
        EXPECTED_NAMES[2]: (
            "forall p c e. "
            f"({valuation2}) -> ~(e = 0) -> ({result2})"
        ),
        EXPECTED_NAMES[3]: (
            "forall p c e. "
            f"({prime3}) -> ~(c = 0) -> ({valuation3}) -> "
            f"({divides3}) -> ~(e = 0)"
        ),
        EXPECTED_NAMES[4]: (
            "forall n s q c p. "
            f"({exclusion4}) -> ({prime4}) -> ({central4}) -> "
            f"({divides4}) -> (({small4}) \\/ "
            f"((({above_small4}) /\\ ({middle4})) \\/ "
            f"(({above_middle4}) /\\ ({row4}))))"
        ),
    }


@lru_cache(maxsize=None)
def _candidate_pool(root_name: str) -> tuple[TheoremSpec, ...]:
    index = EXPECTED_NAMES.index(root_name)
    rows = (*_prior_specs(), *_specs()[: index + 1])
    assert len({row.name for row in rows}) == len(rows)
    return rows


@lru_cache(maxsize=None)
def _blueprint(root_name: str) -> tuple[
    tuple[str, ...],
    tuple[Formula, ...],
    tuple[tuple[int, ...], ...],
    tuple[tuple[int, ...], ...],
    tuple[str, ...],
    int,
    str,
]:
    public = _specs_by_name()
    candidates = {row.name: row for row in _candidate_pool(root_name)}
    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(name: str) -> None:
        if name in public:
            stable_names.add(name)
            return
        item = candidates.get(name)
        assert item is not None, (root_name, name)
        mark = marks.get(name, 0)
        assert mark != 1, (root_name, name)
        if mark == 2:
            return
        marks[name] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[name] = 2
        candidate_order.append(name)

    visit(root_name)
    names = tuple(sorted(stable_names)) + tuple(candidate_order)
    positions = {name: index for index, name in enumerate(names)}
    kinds = tuple(
        "stable_atomic" if name in stable_names else "candidate_body"
        for name in names
    )
    specs = tuple(
        public[name] if name in stable_names else candidates[name]
        for name in names
    )
    targets = tuple(_closed_formula(row.statement) for row in specs)
    dependencies = tuple(
        ()
        if kind == "stable_atomic"
        else tuple(positions[dependency] for dependency in row.dependencies)
        for kind, row in zip(kinds, specs, strict=True)
    )
    depths: list[int] = []
    for node_id, node_dependencies in enumerate(dependencies):
        assert all(dependency < node_id for dependency in node_dependencies)
        depths.append(
            0
            if not node_dependencies
            else 1 + max(depths[item] for item in node_dependencies)
        )
    layer_lists = [[] for _ in range(1 + max(depths, default=0))]
    for node_id, depth in enumerate(depths):
        layer_lists[depth].append(node_id)
    layers = tuple(tuple(layer) for layer in layer_lists)
    topology_rows = (
        "\x1f".join(
            (
                str(node_id),
                name,
                kinds[node_id],
                specs[node_id].statement,
                "\x1e".join(
                    names[dependency]
                    for dependency in dependencies[node_id]
                ),
            )
        )
        for node_id, name in enumerate(names)
    )
    topology = sha256("\x1c".join(topology_rows).encode()).hexdigest()
    return (
        names,
        targets,
        dependencies,
        layers,
        kinds,
        positions[root_name],
        topology,
    )


def _dependency_curried_body(
    item: TheoremSpec,
    targets_by_name: dict[str, Formula],
) -> Proof:
    target = targets_by_name[item.name]
    for dependency in reversed(item.dependencies):
        target = Imp(targets_by_name[dependency], target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        assert tactic != "use"
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


@lru_cache(maxsize=None)
def _bundle(root_name: str) -> LayeredReplayBundle:
    names, targets, dependencies, _layers, kinds, root, _topology = (
        _blueprint(root_name)
    )
    public = _specs_by_name()
    candidates = {row.name: row for row in _candidate_pool(root_name)}
    targets_by_name = dict(zip(names, targets, strict=True))
    nodes = []
    for node_id, name in enumerate(names):
        body = (
            replay(name).certificate
            if kinds[node_id] == "stable_atomic"
            else _dependency_curried_body(candidates[name], targets_by_name)
        )
        nodes.append(
            LayeredReplayNode(
                node_id=node_id,
                target=targets[node_id],
                dependencies=dependencies[node_id],
                body=body,
            )
        )
        if kinds[node_id] == "stable_atomic":
            assert replay(name).spec == public[name]
    return LayeredReplayBundle(tuple(nodes), root)


def test_bertrand_central_prime_support_source_and_rfc_pins() -> None:
    root = Path(__file__).resolve().parents[3]
    library = root / "peano-lab" / "py" / "peano_lab" / "library"
    for filename, expected in SOURCE_PINS.items():
        actual = sha256((library / filename).read_bytes()).hexdigest()
        assert actual == expected, filename
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_central_prime_support_surfaces_are_exact() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert tuple(row.statement for row in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {row.name: row.dependencies for row in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert all(_closed_formula(row.statement) for row in rows)
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        entry.spec.name for entry in editions_v10.ALPHA_ENTRIES
    }


def test_bertrand_central_prime_support_topology_is_exact() -> None:
    rows = _table(_specs())
    assert rows[EXPECTED_NAMES[0]].script.count(
        "apply choose_factorial_bridge"
    ) == 1
    assert rows[EXPECTED_NAMES[0]].script.count("apply multiple_trans") == 1
    assert rows[EXPECTED_NAMES[2]].script.count(
        "apply power_divides_exponent_antitone"
    ) == 1
    assert rows[EXPECTED_NAMES[4]].script.count("specialize le_total p") == 2
    assert rows[EXPECTED_NAMES[4]].script.count(
        "apply le_eq_or_lt"
    ) == 2
    assert not any(
        command.startswith("rewrite hcentral at")
        or command.startswith("rewrite hF_witness at")
        for row in rows.values()
        for command in row.script
    )


def test_bertrand_central_prime_support_receipts_are_shaped() -> None:
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


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_prime_support_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CENTRAL PRIME SUPPORT {name} ARTIFACT actual={actual!r}")
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_prime_support_bodies_are_frozen(name: str) -> None:
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
        label=f"central prime-support body {name}",
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
    print(
        f"CENTRAL PRIME SUPPORT {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
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
assert len(LIVE_EDGES) == 21


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_central_prime_support_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(
            entry for entry in item.dependencies if entry != dependency
        ),
    )
    assert len(shortened.dependencies) + 1 == len(item.dependencies)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_prime_support_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    false_item = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((false_item,), core=_row_core(name))


def _mutations() -> dict[str, str]:
    expected = _expected_statements()
    result: dict[str, str] = {}

    variables0 = ("n", "c", "p")
    old0 = _le_term(
        "p", "n + n", tag="bcpdl_result", variables=variables0
    )
    new0 = _le_term(
        "S p", "n + n", tag="bcpdl_result", variables=variables0
    )
    assert expected[EXPECTED_NAMES[0]].count(old0) == 1
    result[EXPECTED_NAMES[0]] = expected[EXPECTED_NAMES[0]].replace(old0, new0)

    old1 = _no_bertrand(
        variables0, tag="bnbcpdl_exclusion", upper="n + n"
    )
    new1 = _no_bertrand(
        variables0, tag="bnbcpdl_exclusion", upper="n"
    )
    assert expected[EXPECTED_NAMES[1]].count(old1) == 1
    result[EXPECTED_NAMES[1]] = expected[EXPECTED_NAMES[1]].replace(old1, new1)

    variables2 = ("p", "c", "e")
    old2 = _divides_term(
        "p", "c", tag="bpvnedb_result", variables=variables2
    )
    new2 = _divides_term(
        "S p", "c", tag="bpvnedb_result", variables=variables2
    )
    assert expected[EXPECTED_NAMES[2]].count(old2) == 1
    result[EXPECTED_NAMES[2]] = expected[EXPECTED_NAMES[2]].replace(old2, new2)

    head3 = expected[EXPECTED_NAMES[3]].rsplit(" -> ", 1)[0]
    result[EXPECTED_NAMES[3]] = f"{head3} -> e = 0"

    variables4 = ("n", "s", "q", "c", "p")
    old4 = _no_bertrand(
        variables4, tag="bnbcpdr_exclusion", upper="n + n"
    )
    new4 = _no_bertrand(
        variables4, tag="bnbcpdr_exclusion", upper="n"
    )
    assert expected[EXPECTED_NAMES[4]].count(old4) == 1
    result[EXPECTED_NAMES[4]] = expected[EXPECTED_NAMES[4]].replace(old4, new4)
    return result


MUTATIONS = _mutations()


def _is_prime(value: int) -> bool:
    return value >= 2 and all(
        value % divisor for divisor in range(2, int(value**0.5) + 1)
    )


def _valuation(base: int, value: int) -> int:
    result = 0
    while value and value % base == 0:
        value //= base
        result += 1
    return result


def test_bertrand_central_prime_support_mutations_have_fixtures() -> None:
    assert comb(2, 1) == 2 and _is_prime(2) and 2 % 2 == 0
    assert not (3 <= 2)
    assert comb(4, 2) == 6 and _is_prime(3) and 6 % 3 == 0
    assert not any(2 < candidate <= 2 for candidate in range(8))
    assert _valuation(2, 2) == 1 and 2 % 2 == 0 and 2 % 3 != 0
    assert not (1 == 0)
    assert not (3 <= 0)
    assert not (3 <= 2)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_prime_support_mutations_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    old = _closed_formula(item.statement)
    new = _closed_formula(MUTATIONS[name])
    assert old != new
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=MUTATIONS[name]),),
            core=_row_core(name),
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_prime_support_layered_closures_are_frozen(
    name: str,
) -> None:
    names, targets, dependencies, layers, kinds, root, topology = _blueprint(
        name
    )
    assert names[root] == name
    assert targets[root] == _closed_formula(_table(_specs())[name].statement)
    assert tuple(names[item] for item in dependencies[root]) == (
        EXPECTED_DEPENDENCIES[name]
    )
    assert root in layers[-1]
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    interned = intern_layered_replay_bodies(
        _bundle(name),
        targets[root],
        limits=limits,
    )
    assert type(interned) is LayeredReplayBundle
    targets_by_id = {node.node_id: node.target for node in interned.nodes}
    for node in interned.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(targets_by_id[dependency], body_target)
        assert check((), node.body, body_target)
        assert not any(type(item) is DNE for item in _walk(node.body))
    compiled = compile_layered_replay(
        interned,
        targets[root],
        limits=limits,
    )
    assert type(compiled) is LayeredReplayCandidate
    assert compiled.layers == layers
    assert check((), compiled.certificate, compiled.target)
    assert not any(type(item) is DNE for item in _walk(compiled.certificate))
    assert compiled.proof_nodes <= MAX_LIVE_PROOF_NODES
    assert compiled.proof_depth <= MAX_LIVE_PROOF_DEPTH
    assert compiled.proof_objects <= MAX_LIVE_PROOF_OBJECTS
    root_node = interned.nodes[root]
    assert len(root_node.dependencies) == EXPECTED_DIRECT_EDGES[name]
    for index in range(len(root_node.dependencies)):
        broken_dependencies = list(root_node.dependencies)
        broken_dependencies[index] = -1
        broken_nodes = list(interned.nodes)
        broken_nodes[root] = replace(
            root_node,
            dependencies=tuple(broken_dependencies),
        )
        broken = LayeredReplayBundle(tuple(broken_nodes), root)
        assert compile_layered_replay(
            broken,
            targets[root],
            limits=limits,
        ) is None
    actual = (
        compiled.proof_nodes,
        compiled.proof_depth,
        compiled.proof_objects,
        compiled.proof_edges,
        compiled.reused_objects,
        compiled.proof_annotation_occurrences,
        compiled.proof_envelope_depth,
        _proof_dag_sha256(compiled.certificate),
        topology,
    )
    print(f"CENTRAL PRIME SUPPORT {name} LAYERED actual={actual!r}")
    assert EXPECTED_LAYERED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_LAYERED_CLOSURES[name]
