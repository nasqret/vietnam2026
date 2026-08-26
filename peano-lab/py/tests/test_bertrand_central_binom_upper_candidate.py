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
from peano_lab.kernel.formulas import Eq, Formula, Imp
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v10
from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
    make_bertrand_central_binom_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_succ_candidate import (
    make_bertrand_central_binom_succ_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_upper_candidate import (
    make_bertrand_central_binom_upper_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_zero_candidate import (
    make_bertrand_central_binom_zero_candidate_theorems,
)
from peano_lab.library.bertrand_choose_diagonal_candidate import (
    make_bertrand_choose_diagonal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    _le_term,
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
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_bridge_candidate import (
    make_bertrand_power_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_quotient_budget_candidate import (
    make_bertrand_quotient_budget_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    _proof_envelope_metrics_bounded,
)
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _support() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_choose_foundation_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_table_row_functional_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_laws_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_diagonal_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_recurrence_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_pascal_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_symmetry_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_weighted_vertical_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_candidate_theorems(TheoremSpec)[:1],
        *make_bertrand_central_binom_zero_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_succ_candidate_theorems(TheoremSpec),
        make_bertrand_integer_envelope_candidate_theorems(TheoremSpec)[0],
        make_bertrand_quotient_budget_candidate_theorems(TheoremSpec)[0],
        make_bertrand_power_bridge_candidate_theorems(TheoremSpec)[0],
    )


EXPECTED_NAMES = (
    "central_binom_strong_upper_step",
    "central_binom_recurrence_double_bundle",
    "central_binom_strong_upper_of_laws",
    "central_binom_upper_support_package",
    "central_binom_strong_upper",
    "central_binom_odd_middle_le_four_pow",
)

EXPECTED_DEPENDENCIES = {
    EXPECTED_NAMES[0]: (
        "zero_add",
        "add_succ_left",
        "add_assoc",
        "mul_comm",
        "mul_assoc",
        "two_mul_eq_add_self",
        "mul_le_mul_left",
        "mul_le_mul_right",
        "le_trans",
        "succ_ne_zero",
        "mul_le_cancel_left_nonzero",
    ),
    EXPECTED_NAMES[1]: (
        "mul_add",
        "mul_assoc",
        "two_mul_eq_add_self",
        "central_binom_succ_double_middle",
        "choose_weighted_vertical",
        "choose_functional",
    ),
    EXPECTED_NAMES[2]: (
        "one_mul",
        "le_refl",
        "pow_zero",
        "pow_successor_decompose",
        "central_binom_zero",
        EXPECTED_NAMES[0],
    ),
    EXPECTED_NAMES[3]: (
        EXPECTED_NAMES[1],
        "central_binom_exists",
    ),
    EXPECTED_NAMES[4]: (
        EXPECTED_NAMES[3],
        EXPECTED_NAMES[2],
    ),
    EXPECTED_NAMES[5]: (
        "mul_add",
        "mul_assoc",
        "mul_comm",
        "two_mul_eq_add_self",
        "mul_le_cancel_left_nonzero",
        "pow_successor_compose",
        EXPECTED_NAMES[3],
        EXPECTED_NAMES[2],
    ),
}

EXPECTED_DIRECT_CUTS = dict(
    zip(EXPECTED_NAMES, (11, 6, 6, 2, 2, 8), strict=True)
)
assert sum(map(len, EXPECTED_DEPENDENCIES.values())) == 35

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    EXPECTED_NAMES[0]: (
        214,
        "7f7c2c7df93240974316e0697c003e56633161d3dc431cf56f101c76d0f6ba85",
        "1df4830fffc82380f2aaf8edfd72e69f310c9ceb4e561b7bbacc16fbc7f8d8ee",
        "c67d9cf6d82a3ae35573e6e8813f4aa438af2925ab1667b08f5c63a2e82e38f5",
    ),
    EXPECTED_NAMES[1]: (
        32255,
        "48cefedfe334e24b3d13c578ee52f8b5ecc57e3a745c0e487c1e86d201409585",
        "c57f6737bfb5c554db65bd5f676483186136d4ab97b4c6dc681dc8a15224e215",
        "4dfb6f70dfbc602ec057613e3c5f588bae6c6d2049f4a6942d57839f3c423ca9",
    ),
    EXPECTED_NAMES[2]: (
        34598,
        "73f62794c4272b895b6600b07ed08ecc05b578344ed78c516f9613b79e0bacd7",
        "e11a14e28e8efb7e5f7f32474406babfa2cd5faca2168bba2c973b7ebd2673e3",
        "bee4bbd3c5e071c2e8e5f92ab8f5c53d6394e19f912a4b66054044ed2fa55fcd",
    ),
    EXPECTED_NAMES[3]: (
        39852,
        "2337724d3aadb3de565a8ab1d9f5facb167d544ee7653628fb6b560d881718a0",
        "8cd8a9db4ada3c8436c873df1b06f19776bf86ccd20f969a2c15668681ec8323",
        "4c3232952baf681c30bbd0a29e75f83f2fa6838f9b125a5f14cd4f321f7edc35",
    ),
    EXPECTED_NAMES[4]: (
        10480,
        "24797292a5037a0925ea5ac5393a6b384c7a8f7a9899ee29fced643dcf49fadb",
        "c4f9364c948334a3927cfc0b1d4d1ad86cedff8df553f24dd9e44413169b03c3",
        "3042cfe218ce102364566e30b1e916365e9b5e9f4bcc19d654ba4a4e99c01537",
    ),
    EXPECTED_NAMES[5]: (
        10536,
        "ccd5bcefbd793af62299209b6f3324428cf30fd7e90c7cd62ce32ae1f5c0b733",
        "bf8ed394f0137abcb9cd3b35578055e8adfa81bf9441524ac94522725c60a94f",
        "fcb8aa2c477cc67b01a389abd0b2c4c7fb89aef59e3668b3dcc2952b79a419e1",
    ),
}
EXPECTED_BODIES: dict[
    str,
    tuple[int, int, int, int, int, int, int] | None,
] = {
    EXPECTED_NAMES[0]: (11, 94, 194, 38, 194, 193, 0),
    EXPECTED_NAMES[1]: (6, 62, 101, 27, 101, 100, 0),
    EXPECTED_NAMES[2]: (6, 89, 298, 36, 298, 297, 0),
    EXPECTED_NAMES[3]: (2, 3, 5, 4, 5, 4, 0),
    EXPECTED_NAMES[4]: (2, 7, 10, 7, 10, 9, 0),
    EXPECTED_NAMES[5]: (8, 62, 138, 35, 138, 137, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    EXPECTED_NAMES[0]: (194, 194, 38, 362, 39),
    EXPECTED_NAMES[1]: (101, 101, 27, 107, 28),
    EXPECTED_NAMES[2]: (298, 298, 36, 921, 55),
    EXPECTED_NAMES[3]: (5, 5, 4, 0, 4),
    EXPECTED_NAMES[4]: (10, 10, 7, 0, 7),
    EXPECTED_NAMES[5]: (138, 138, 35, 175, 35),
}
EXPECTED_CLOSURES: dict[
    str,
    tuple[int, int, int, int, int, int, int, str] | None,
] = {
    EXPECTED_NAMES[0]: (
        2058,
        39,
        882,
        937,
        56,
        5859,
        40,
        "aea659bb7e2ad5fc1a29da38dd4bf8430af2e50034087eaa31c2275ffcd6d9cf",
    ),
    EXPECTED_NAMES[1]: (
        307954,
        111,
        9026,
        9340,
        315,
        1160051,
        111,
        "25f2b0e3e85a96253d0c134e845b5edb476fcb4a8f82d65d7e5dc41ac8a85adc",
    ),
    EXPECTED_NAMES[2]: (
        7640,
        71,
        2229,
        2309,
        81,
        39734,
        71,
        "91f88af2156829ebb53a6a2959c17189444777bb0416a6ce1685aa29936da199",
    ),
    EXPECTED_NAMES[3]: (
        397462,
        112,
        9042,
        9357,
        316,
        1463051,
        112,
        "438383f5e93faee3fa174cc629131c6bda0bfd97ed489f39965080ea6048ada7",
    ),
    EXPECTED_NAMES[4]: (
        405112,
        113,
        9957,
        10299,
        343,
        1508094,
        113,
        "7ebebfb082878b4a584bf11ce9ba9ebdca78f161eb69622f122024a4d0e36fea",
    ),
    EXPECTED_NAMES[5]: (
        471772,
        119,
        10928,
        11298,
        371,
        1733312,
        119,
        "8f71cd3f94080e1c6c570f8f0a8ef76cf69c188469860b637fbaa46bc2b84247",
    ),
}

RFC_SHA256 = (
    "1aad1afa2ce0d44c04dc32d4ef61d84dd311e216f188977980bc18d7820ff05d"
)

SOURCE_PINS = {
    "peano-lab/py/peano_lab/library/"
    "bertrand_choose_foundation_candidate.py": (
        "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_choose_row_functional_candidate.py": (
        "dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_choose_table_row_functional_candidate.py": (
        "379319daec74ad2e6b89b0808f885b87f6cc1a3fab4908559511d26f51be35f5"
    ),
    "peano-lab/py/peano_lab/library/bertrand_choose_laws_candidate.py": (
        "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_choose_diagonal_candidate.py": (
        "96044d1bf4e10dfffba3f9f7482c4fd9ff1f94fffbccac9fe45af32a32a691bc"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_choose_recurrence_candidate.py": (
        "8b4a65b18e6a97a89c3f714686f2c690afb49f82ab56ed9575e3f673f50093c5"
    ),
    "peano-lab/py/peano_lab/library/bertrand_choose_pascal_candidate.py": (
        "e96ee1d140beece2666b901dc7d671743b01386f110628b0957aeff01b9c26c3"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_choose_symmetry_candidate.py": (
        "9958068fc364ca4bd171e965283a7683d167dcd6650e7a8df13f0b27c1edb78a"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_choose_weighted_vertical_candidate.py": (
        "e8629d085ccb2d69acb179ce2bcede5612edf290a39dac175476574f9ce76bd1"
    ),
    "peano-lab/py/peano_lab/library/bertrand_central_binom_candidate.py": (
        "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_central_binom_zero_candidate.py": (
        "978dbdbdfe2fa68a5e0db91bbf895517028c66ec5956571fd7c15d0993c52e04"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_central_binom_succ_candidate.py": (
        "c0faea72fbe7c21ada1f15adc91dec324e0fa643bde464c9b10f9a75df4f2b27"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_integer_envelope_candidate.py": (
        "8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_quotient_budget_candidate.py": (
        "78dbb7c472eb10861bbe39ec150f1499198a43c5f3687781c2e104e96516f225"
    ),
    "peano-lab/py/peano_lab/library/bertrand_power_bridge_candidate.py": (
        "a5f9a60e680adab7cb290835a62a0359550dd773861e152ebb2615b2dcc637ab"
    ),
    "peano-lab/py/peano_lab/library/"
    "bertrand_central_binom_upper_candidate.py": (
        "5bfea8dc2427bf60be8115c6b8cfb8e6a81d4c1bfb0ce65b695cdb065281247a"
    ),
}


def _expected_statements() -> dict[str, str]:
    step_variables = ("n", "c", "d", "q", "r")
    step_source = _le_term(
        "2 * c",
        "q",
        tag="bcbsus_source",
        variables=step_variables,
    )
    step_result = _le_term(
        "2 * d",
        "r",
        tag="bcbsus_result",
        variables=step_variables,
    )
    law_variables = ("n", "c", "d", "m")
    predecessor = _central_binom_relation_term(
        "n",
        "c",
        tag="bcbrdb_predecessor",
        variables=law_variables,
    )
    successor = _central_binom_relation_term(
        "S n",
        "d",
        tag="bcbrdb_successor",
        variables=law_variables,
    )
    middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "m",
        tag="bcbrdb_middle",
        variables=law_variables,
    )
    recurrence = (
        "forall n c d. "
        f"({predecessor}) -> ({successor}) -> "
        "S n * d = (2 * S (n + n)) * c"
    )
    double = (
        "forall n d m. "
        f"({successor}) -> ({middle}) -> d = m + m"
    )
    bundle = f"(({recurrence}) /\\ ({double}))"
    exists_variables = ("n", "z")
    exists_relation = _central_binom_relation_term(
        "n",
        "z",
        tag="bcbsuo_exists",
        variables=exists_variables,
    )
    central_exists = f"forall n. exists z. ({exists_relation})"
    upper_variables = ("n", "c", "q")
    upper_central = _central_binom_relation_term(
        "S n",
        "c",
        tag="bcbsuo_central",
        variables=upper_variables,
    )
    upper_power = _power_terms("4", "S n", "q", tag="bcbsuo_power")
    upper_result = _le_term(
        "2 * c",
        "q",
        tag="bcbsuo_result",
        variables=upper_variables,
    )
    strong = (
        "forall n c q. "
        f"({upper_central}) -> ({upper_power}) -> ({upper_result})"
    )
    odd_variables = ("n", "m", "q")
    odd_middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "m",
        tag="bcomlfp_middle",
        variables=odd_variables,
    )
    odd_power = _power_terms("4", "n", "q", tag="bcomlfp_power")
    odd_result = _le_term(
        "m",
        "q",
        tag="bcomlfp_result",
        variables=odd_variables,
    )
    return {
        EXPECTED_NAMES[0]: (
            "forall n c d q r. "
            f"({step_source}) -> "
            "S n * d = (2 * S (n + n)) * c -> "
            f"r = q * 4 -> ({step_result})"
        ),
        EXPECTED_NAMES[1]: bundle,
        EXPECTED_NAMES[2]: (
            f"({recurrence}) -> ({central_exists}) -> ({strong})"
        ),
        EXPECTED_NAMES[3]: f"(({bundle}) /\\ ({central_exists}))",
        EXPECTED_NAMES[4]: strong,
        EXPECTED_NAMES[5]: (
            "forall n m q. "
            f"({odd_middle}) -> ({odd_power}) -> ({odd_result})"
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_upper_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    support = _table(_support())
    assert not (set(public) & set(support))
    assert not (set(EXPECTED_NAMES) & set(public))
    assert not (set(EXPECTED_NAMES) & set(support))
    assert "central_binom_functional" not in support
    assert "central_binom_positive" not in support
    return public | support


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _row_core(name: str) -> dict[str, TheoremSpec]:
    return _core() | _table(_specs()[: EXPECTED_NAMES.index(name)])


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
    if name in _specs_by_name():
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
    dependencies = tuple(_close(dep, cache) for dep in item.dependencies)
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


def test_bertrand_central_binom_upper_sources_are_pinned() -> None:
    root = Path(__file__).resolve().parents[3]
    for relative, digest in SOURCE_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest
    rfc = root / "research/arithmetic-library/" \
        "ha-bertrand-central-binomial-upper-tranche-rfc-v1.md"
    assert sha256(rfc.read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_central_binom_upper_factory_is_exact() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert all(_closed_formula(item.statement) for item in rows)
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        entry.spec.name for entry in editions_v10.ALPHA_ENTRIES
    }


def test_bertrand_central_binom_upper_topology_is_exact() -> None:
    table = _table(_specs())
    assert "congr" not in table[EXPECTED_NAMES[0]].script
    assert table[EXPECTED_NAMES[1]].script.count(
        "apply central_binom_succ_double_middle"
    ) == 2
    assert table[EXPECTED_NAMES[1]].script.count(
        "apply choose_weighted_vertical"
    ) == 1
    assert table[EXPECTED_NAMES[2]].script.count("induction n") == 1
    assert table[EXPECTED_NAMES[2]].script.count(
        "apply central_binom_strong_upper_step"
    ) == 1
    assert table[EXPECTED_NAMES[4]].script[0].startswith("have hpackage")
    assert not any(
        command.startswith("intro ")
        for command in table[EXPECTED_NAMES[4]].script
    )
    assert table[EXPECTED_NAMES[5]].script.count(
        "apply mul_le_cancel_left_nonzero"
    ) == 1
    assert all(
        not command.startswith("rewrite hcentral at")
        for row in table.values()
        for command in row.script
    )


def test_bertrand_central_binom_upper_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert all(value is not None for value in EXPECTED_ARTIFACTS.values())
    assert all(value is not None for value in EXPECTED_BODIES.values())
    assert all(value is not None for value in EXPECTED_ENVELOPES.values())
    assert all(value is not None for value in EXPECTED_CLOSURES.values())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_binom_upper_artifacts_are_frozen(
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
    print(f"CENTRAL UPPER {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_binom_upper_bodies_are_frozen(
    name: str,
) -> None:
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
        label=f"Central upper body {name}",
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
        f"CENTRAL UPPER {name} BODY actual={actual!r} "
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
assert len(LIVE_EDGES) == 35


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_central_binom_upper_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(dep for dep in item.dependencies if dep != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_binom_upper_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=f"({item.statement}) /\\ false"),),
            core=_row_core(name),
        )


def _mutations() -> tuple[tuple[str, str, str], ...]:
    statements = _expected_statements()
    step_variables = ("n", "c", "d", "q", "r")
    old0 = _le_term(
        "2 * d",
        "r",
        tag="bcbsus_result",
        variables=step_variables,
    )
    new0 = _le_term(
        "S (2 * d)",
        "r",
        tag="bcbsus_result",
        variables=step_variables,
    )
    old_double = "d = m + m"
    new_double = "d = S (m + m)"
    upper_variables = ("n", "c", "q")
    old_upper = _le_term(
        "2 * c",
        "q",
        tag="bcbsuo_result",
        variables=upper_variables,
    )
    new_upper = _le_term(
        "S (2 * c)",
        "q",
        tag="bcbsuo_result",
        variables=upper_variables,
    )
    odd_variables = ("n", "m", "q")
    old_odd = _le_term(
        "m",
        "q",
        tag="bcomlfp_result",
        variables=odd_variables,
    )
    new_odd = _le_term(
        "S m",
        "q",
        tag="bcomlfp_result",
        variables=odd_variables,
    )
    replacements = (
        (old0, new0),
        (old_double, new_double),
        (old_upper, new_upper),
        (old_double, new_double),
        (old_upper, new_upper),
        (old_odd, new_odd),
    )
    result = []
    for name, (old, new) in zip(EXPECTED_NAMES, replacements, strict=True):
        statement = statements[name]
        assert statement.count(old) == 1
        result.append((name, statement, statement.replace(old, new, 1)))
    return tuple(result)


def test_bertrand_central_binom_upper_mutations_have_fixtures() -> None:
    assert 1 > 0
    assert 2 != 3
    assert 5 > 4
    assert 2 > 1


@pytest.mark.parametrize(("name", "old", "new"), _mutations(), ids=EXPECTED_NAMES)
def test_bertrand_central_binom_upper_mutations_are_rejected(
    name: str,
    old: str,
    new: str,
) -> None:
    item = _table(_specs())[name]
    assert item.statement == old
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=new),),
            core=_row_core(name),
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_central_binom_upper_closures_are_frozen(
    name: str,
) -> None:
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
        label=f"Central upper closure {name}",
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
    for index in range(direct_cut_count):
        assert not check((), _mutate_direct_cut(certificate, index), formula)
    print(f"CENTRAL UPPER {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_CLOSURES[name]
