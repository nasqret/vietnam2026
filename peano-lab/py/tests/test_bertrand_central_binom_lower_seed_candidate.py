"""Fail-closed audit for the exact fourth central-binomial lower seed."""

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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Add, Zero, parse_term_in_context, pretty_term
from peano_lab.library import (
    alpha_enrollment_v7,
    bertrand_central_binom_candidate as central_module,
    bertrand_central_binom_growth_candidate as growth_module,
    bertrand_central_binom_lower_seed_candidate as module,
    bertrand_central_binom_zero_candidate as central_zero_module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    editions_v7,
    power_algebra_theorems as power_algebra_module,
    theorems as stable_module,
)
from peano_lab.library.bertrand_central_binom_candidate import (
    make_bertrand_central_binom_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_growth_candidate import (
    make_bertrand_central_binom_growth_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_lower_seed_candidate import (
    make_bertrand_central_binom_lower_seed_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_zero_candidate import (
    make_bertrand_central_binom_zero_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    make_bertrand_choose_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    make_bertrand_choose_laws_candidate_theorems,
)
from peano_lab.library.bertrand_choose_row_functional_candidate import (
    make_bertrand_choose_row_functional_candidate_theorems,
)
from peano_lab.library.bertrand_choose_table_row_functional_candidate import (
    make_bertrand_choose_table_row_functional_candidate_theorems,
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


POW_EXACT = "pow_four_four_exact"
CENTRAL_EXACT = "central_binom_four_weighted_of_recurrence"
STRICT_SEED = "four_pow_central_seed_package"
EXPECTED_NAMES = (POW_EXACT, CENTRAL_EXACT, STRICT_SEED)
EXPECTED_DEPENDENCIES = {
    POW_EXACT: ("pow_successor_decompose", "pow_two"),
    CENTRAL_EXACT: (
        "one_mul",
        "mul_left_cancel_nonzero",
        "central_binom_zero",
    ),
    STRICT_SEED: (
        "mul_assoc",
        "mul_lt_mul_right_nonzero",
        "central_binom_exists",
        POW_EXACT,
        CENTRAL_EXACT,
    ),
}
EXPECTED_DIRECT_CUTS = {POW_EXACT: 2, CENTRAL_EXACT: 3, STRICT_SEED: 5}
EXPECTED_ARTIFACTS = {
    POW_EXACT: (
        2640,
        "c68410d517781bd7640ea97e4a1dc767c48d6d70bc344ac8e11f474b40ec0c4b",
        "5c4e1a5fe31aa5daba1ecf4d9d20693530ef22d00e393eb0f6f22653ea338b0b",
        "77ada3fe5c28322555605334bebbc1ef5e086825175ca16042024fc7a4fae4ae",
    ),
    CENTRAL_EXACT: (
        35267,
        "fb8059be82b56c4866cd79ebbd84f02b0b317ef50b027d2b8a3972d1cc6d9d16",
        "a93273485d8cbebfbf28666213c590cc92d96acb2e39910d5788ddbe581df515",
        "3b508557060e851bff073b076a86f95595707fe32cb13689f9d0d10c6f5b7e38",
    ),
    STRICT_SEED: (
        38327,
        "95bd5dd9be51fa5c88f9c3d24f99e552f16aa2a32732b2e43c308a194176e16f",
        "dacc6fed7fb3c095f90e115028f7c20cb71e8f36060f8a9c06e91c0ecdad0cd4",
        "265cf723566885f74389dcfe3e34713c9121e12e33a6b337785fdcb9538c4dff",
    ),
}
EXPECTED_BODIES = {
    POW_EXACT: (2, 22, 45, 16, 45, 44, 0),
    CENTRAL_EXACT: (3, 67, 1446, 85, 1446, 1445, 0),
    STRICT_SEED: (5, 35, 1610, 152, 1610, 1609, 0),
}
EXPECTED_ENVELOPES = {
    POW_EXACT: (45, 45, 16, 165, 20),
    CENTRAL_EXACT: (1446, 1446, 85, 5914, 90),
    STRICT_SEED: (1610, 1610, 152, 8972, 157),
}
EXPECTED_CLOSURES = {
    POW_EXACT: (
        9046,
        70,
        1180,
        1228,
        49,
        37924,
        70,
        "d8c330d5bad90dea36d3e0cb8ba10d953e74f1a84544410aa164e87e824c382c",
    ),
    CENTRAL_EXACT: (
        3164,
        85,
        2625,
        2669,
        45,
        18673,
        90,
        "7cf1e9038d442f9d976d87c6d41f536a37fc88c4e4170c424ad40576fe587220",
    ),
    STRICT_SEED: (
        104222,
        152,
        9326,
        9593,
        268,
        377153,
        157,
        "d2896742534d81509e2c382250c5fb01bb6998d4e07a5b5e7dbaeb9e8b96f56d",
    ),
}

SOURCE_PINS = {
    foundation: (
        "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
    ),
    row_functional_module: (
        "dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf"
    ),
    table_functional_module: (
        "379319daec74ad2e6b89b0808f885b87f6cc1a3fab4908559511d26f51be35f5"
    ),
    laws_module: "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d",
    growth_module: "de43bd809ebd10cc31fc2ebcc12df10328e3571f491446545e34585b5a6fb66b",
    central_module: "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e",
    central_zero_module: (
        "978dbdbdfe2fa68a5e0db91bbf895517028c66ec5956571fd7c15d0993c52e04"
    ),
    power_algebra_module: (
        "6566c3539a18801c32d0a3ae7b6abe242bb8cf62e95184271680f0303b6fc302"
    ),
    module: "6bb371e4d772272a4f14937719882a61590b3ee3f1869e26ce48661115a8f1f7",
}


def _pa_beta(code: str, scale: str, index: str, value: str, tag: str) -> str:
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists pa_h_{tag}. pa_h_{tag} + S ({value}) = {modulus}) /\\ "
        f"exists pa_q_{tag}. {code} = pa_q_{tag} * {modulus} + ({value}))"
    )


def _pa_lt(left: str, right: str, tag: str) -> str:
    return f"exists pa_lt_{tag}. pa_lt_{tag} + S {left} = {right}"


def _pa_repeat(code: str, scale: str, value: str, length: str, tag: str) -> str:
    index = f"pa_i_{tag}"
    bound = _pa_lt(index, length, f"{tag}_bound")
    decoded = _pa_beta(code, scale, index, value, f"{tag}_decoded")
    return f"forall {index}. ({bound}) -> ({decoded})"


def _pa_product(code: str, scale: str, length: str, result: str, tag: str) -> str:
    u, v = f"pa_u_{tag}", f"pa_v_{tag}"
    i, p, r, s = (f"pa_{stem}_{tag}" for stem in ("i", "p", "r", "s"))
    start = _pa_beta(u, v, "0", "1", f"{tag}_start")
    terminal = _pa_beta(u, v, length, result, f"{tag}_terminal")
    bound = _pa_lt(i, length, f"{tag}_bound")
    factor = _pa_beta(code, scale, i, p, f"{tag}_factor")
    partial = _pa_beta(u, v, i, r, f"{tag}_partial")
    successor = _pa_beta(u, v, f"S {i}", s, f"{tag}_successor")
    return (
        f"exists {u} {v}. (({start}) /\\ (({terminal}) /\\ "
        f"forall {i}. ({bound}) -> exists {p} {r} {s}. "
        f"(({factor}) /\\ (({partial}) /\\ (({successor}) /\\ "
        f"{s} = {r} * {p})))))"
    )


def _power(base: str, exponent: str, result: str, tag: str) -> str:
    code, scale = f"pa_b_{tag}", f"pa_c_{tag}"
    repeat = _pa_repeat(code, scale, base, exponent, f"{tag}_repeat")
    product = _pa_product(code, scale, exponent, result, f"{tag}_product")
    return f"exists {code} {scale}. (({repeat}) /\\ ({product}))"


def _central(index: str, value: str, tag: str, variables: tuple[str, ...]) -> str:
    context = list(variables)
    index_term = parse_term_in_context(index, context)
    value_term = parse_term_in_context(value, context)
    rendered_index = pretty_term(index_term, context).replace("·", "*")
    rendered_value = pretty_term(value_term, context).replace("·", "*")
    doubled = pretty_term(Add(index_term, index_term), context).replace("·", "*")
    return foundation._choose_relation_term(
        doubled,
        rendered_index,
        rendered_value,
        tag=tag,
        variables=variables,
    )


def _lt(left: str, right: str, tag: str) -> str:
    gap = f"bcf_lt_gap_{tag}"
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _central_recurrence() -> str:
    variables = ("n", "a", "b")
    predecessor = _central(
        "n", "a", "bcb4we_recurrence_predecessor", variables
    )
    successor = _central(
        "S n", "b", "bcb4we_recurrence_successor", variables
    )
    return (
        "forall n a b. "
        f"({predecessor}) -> ({successor}) -> "
        "S n * b = (2 * S (n + n)) * a"
    )


def _central_exists() -> str:
    relation = _central("n", "z", "bcb4we_exists", ("n", "z"))
    return f"forall n. exists z. ({relation})"


def _relations() -> dict[str, str]:
    return {
        "power_four": _power("4", "4", "p", "bpf4e_source"),
        "central_four": _central("4", "c", "bcb4we_source", ("c",)),
        "recurrence": _central_recurrence(),
        "central_exists": _central_exists(),
        "seed_power": _power("4", "4", "p", "bfplcb4_power"),
        "seed_central": _central(
            "4", "c", "bfplcb4_central", ("p", "c")
        ),
        "seed_result": _lt("p", "4 * c", "bfplcb4_result"),
    }


def _expected_statements() -> dict[str, str]:
    rel = _relations()
    return {
        POW_EXACT: (
            f"forall p. ({rel['power_four']}) -> p = ((4 * 4) * 4) * 4"
        ),
        CENTRAL_EXACT: (
            f"({rel['recurrence']}) -> ({rel['central_exists']}) -> "
            f"forall c. ({rel['central_four']}) -> "
            "4 * c = (2 * S (3 + 3)) * 20"
        ),
        STRICT_SEED: (
            f"({rel['recurrence']}) -> (({rel['central_exists']}) /\\ "
            f"(forall p c. ({rel['seed_power']}) -> "
            f"({rel['seed_central']}) -> ({rel['seed_result']})))"
        ),
    }


EXPECTED_POWER_SCRIPT = (
    "intro p",
    "intro hpower",
    (
        "have hthree : exists r. "
        f"({_power('4', '3', 'r', 'bpf4e_three')}) /\\ p = r * 4"
    ),
    "apply pow_successor_decompose",
    "refl",
    "exact hpower",
    "cases hthree",
    "cases hthree_witness",
    (
        "have htwo : exists r. "
        f"({_power('4', '2', 'r', 'bpf4e_two')}) /\\ x = r * 4"
    ),
    "apply pow_successor_decompose",
    "refl",
    "exact hthree_witness_left",
    "cases htwo",
    "cases htwo_witness",
    "have htwo_value : x1 = 4 * 4",
    "apply pow_two",
    "refl",
    "exact htwo_witness_left",
    "rewrite hthree_witness_right",
    "rewrite htwo_witness_right",
    "rewrite htwo_value",
    "refl",
)

EXPECTED_CENTRAL_SCRIPT = (
    "intro hrecurrence",
    "intro hcentral_exists",
    "intro c",
    "intro hcentral",
    (
        "have hzero_exists : exists a. "
        f"({_central('0', 'a', 'bcb4we_zero', ('c', 'a'))})"
    ),
    "apply hcentral_exists",
    "cases hzero_exists",
    (
        "have hone_exists : exists a. "
        f"({_central('1', 'a', 'bcb4we_one', ('c', 'a'))})"
    ),
    "apply hcentral_exists",
    "cases hone_exists",
    (
        "have htwo_exists : exists a. "
        f"({_central('2', 'a', 'bcb4we_two', ('c', 'a'))})"
    ),
    "apply hcentral_exists",
    "cases htwo_exists",
    (
        "have hthree_exists : exists a. "
        f"({_central('3', 'a', 'bcb4we_three', ('c', 'a'))})"
    ),
    "apply hcentral_exists",
    "cases hthree_exists",
    "have hzero_value : x = 1",
    "apply central_binom_zero",
    "exact hzero_exists_witness",
    "have hrecurrence_zero : S 0 * x1 = (2 * S (0 + 0)) * x",
    "apply hrecurrence",
    "exact hzero_exists_witness",
    "exact hone_exists_witness",
    "rewrite hzero_value at hrecurrence_zero",
    "specialize one_mul x1",
    "rewrite one_mul at hrecurrence_zero",
    "have hzero_rhs : (2 * S (0 + 0)) * 1 = 2",
    "norm_num",
    "rewrite hzero_rhs at hrecurrence_zero",
    "have hone_value : x1 = 2",
    "exact hrecurrence_zero",
    "have hrecurrence_one : S 1 * x2 = (2 * S (1 + 1)) * x1",
    "apply hrecurrence",
    "exact hone_exists_witness",
    "exact htwo_exists_witness",
    "rewrite hone_value at hrecurrence_one",
    "have hone_rhs : (2 * S (1 + 1)) * 2 = 2 * 6",
    "norm_num",
    "rewrite hone_rhs at hrecurrence_one",
    "have htwo_value : x2 = 6",
    "specialize mul_left_cancel_nonzero 2",
    "apply mul_left_cancel_nonzero",
    "intro htwo_zero",
    "apply PA1",
    "exact htwo_zero",
    "exact hrecurrence_one",
    "have hrecurrence_two : S 2 * x3 = (2 * S (2 + 2)) * x2",
    "apply hrecurrence",
    "exact htwo_exists_witness",
    "exact hthree_exists_witness",
    "rewrite htwo_value at hrecurrence_two",
    "have htwo_rhs : (2 * S (2 + 2)) * 6 = 3 * 20",
    "norm_num",
    "rewrite htwo_rhs at hrecurrence_two",
    "have hthree_value : x3 = 20",
    "specialize mul_left_cancel_nonzero 3",
    "apply mul_left_cancel_nonzero",
    "intro hthree_zero",
    "apply PA1",
    "exact hthree_zero",
    "exact hrecurrence_two",
    "have hrecurrence_three : S 3 * c = (2 * S (3 + 3)) * x3",
    "apply hrecurrence",
    "exact hthree_exists_witness",
    "exact hcentral",
    "rewrite hthree_value at hrecurrence_three",
    "exact hrecurrence_three",
)

EXPECTED_SEED_SCRIPT = (
    "intro hrecurrence",
    "split",
    "exact central_binom_exists",
    "intro p",
    "intro c",
    "intro hpower",
    "intro hcentral",
    "have hpower_value : p = ((4 * 4) * 4) * 4",
    "apply pow_four_four_exact",
    "exact hpower",
    (
        "have hweighted : forall c. "
        f"({_central('4', 'c', 'bcb4we_source', ('c',))}) -> "
        "4 * c = (2 * S (3 + 3)) * 20"
    ),
    "apply central_binom_four_weighted_of_recurrence",
    "exact hrecurrence",
    "exact central_binom_exists",
    "have hcentral_value : 4 * c = (2 * S (3 + 3)) * 20",
    "apply hweighted",
    "exact hcentral",
    (
        "have hsmall : "
        f"{_lt('(4 * 4) * 4', '(2 * S (3 + 3)) * 5', 'bfplcb4_small')}"
    ),
    "exists 5",
    "norm_num",
    (
        "have hscaled : "
        f"{_lt('((4 * 4) * 4) * 4', '((2 * S (3 + 3)) * 5) * 4', 'bfplcb4_scaled')}"
    ),
    "apply mul_lt_mul_right_nonzero",
    "exact hsmall",
    "intro hfour_zero",
    "apply PA1",
    "exact hfour_zero",
    "have hfive_four : 5 * 4 = 20",
    "norm_num",
    (
        "have hassoc : ((2 * S (3 + 3)) * 5) * 4 = "
        "(2 * S (3 + 3)) * (5 * 4)"
    ),
    "apply mul_assoc",
    "rewrite hassoc at hscaled",
    "rewrite hfive_four at hscaled",
    "rewrite hpower_value",
    "rewrite hcentral_value",
    "exact hscaled",
)
EXPECTED_SCRIPTS = {
    POW_EXACT: EXPECTED_POWER_SCRIPT,
    CENTRAL_EXACT: EXPECTED_CENTRAL_SCRIPT,
    STRICT_SEED: EXPECTED_SEED_SCRIPT,
}


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_lower_seed_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_choose_foundation_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_table_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_laws_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_candidate_theorems(TheoremSpec)[:1],
        *make_bertrand_central_binom_zero_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_growth_candidate_theorems(TheoremSpec)[:1],
    )


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    table = {row.name: row for row in rows}
    assert len(table) == len(rows)
    return table


@lru_cache(maxsize=1)
def _base_core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    support = _table(_support_specs())
    assert not (set(public) & set(support))
    assert not (set(EXPECTED_NAMES) & (set(public) | set(support)))
    return public | support


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    core = (
        dict(_specs_by_name())
        if name == POW_EXACT
        else _base_core()
    )
    return core | _table(_specs()[:index])


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _base_core() | _table(_specs())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    target = _closed_formula(item.statement)
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


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    if name in _specs_by_name():
        checked = replay(name)
        return checked.formula, checked.certificate
    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    dependencies = tuple(_close(dep) for dep in item.dependencies)
    for dep_formula, dep_proof in reversed(dependencies):
        body = Cut(dep_formula, formula, dep_proof, body)
    assert check((), body, formula)
    return formula, body


def _children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for field in fields(proof)
        if isinstance((child := getattr(proof, field.name)), Proof)
    )


def _walk(proof: Proof):
    pending, seen = [proof], set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(_children(node))


def _dag_hash(proof: Proof) -> str:
    digests: dict[int, str] = {}
    pending = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        if id(node) in digests:
            continue
        children = _children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend((child, False) for child in children)
            continue
        payload = [type(node).__name__]
        for field in fields(node):
            value = getattr(node, field.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[id(node)] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _corrupt_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_corrupt_cut(proof.body, index - 1))


def test_sources_surfaces_scripts_and_authority_are_exact() -> None:
    for provider, digest in SOURCE_PINS.items():
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest
    rows = _specs()
    assert make_bertrand_central_binom_lower_seed_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    statements = _expected_statements()
    for row in rows:
        assert row.statement == statements[row.name]
        assert row.dependencies == EXPECTED_DEPENDENCIES[row.name]
        assert row.script == EXPECTED_SCRIPTS[row.name]
        parsed, free = parse_formula_with_names(row.statement)
        assert not free and parsed == _closed_formula(row.statement)
        assert not any(
            token in row.statement
            for token in ("Pow(", "Choose(", "CentralBinom(", "<", "^")
        )
        for command in row.script:
            assert not any(
                token in command
                for token in (
                    "DNE", "classical", "by_contra", "sorry", "auto",
                    "compact_arith", "ring", "use ",
                )
            )
    assert module.__all__ == [
        "make_bertrand_central_binom_lower_seed_candidate_theorems"
    ]
    assert len(_support_specs()) == 16
    support_names = set(_table(_support_specs()))
    assert "central_binom_exists" in support_names
    assert "central_binom_zero" in support_names
    assert "mul_lt_mul_right_nonzero" in support_names
    assert "central_binom_succ_recurrence" not in support_names
    assert "four_power_central_recurrence_step" not in support_names
    assert "central_binom_functional" not in support_names
    assert "central_binom_positive" not in support_names
    assert not any("factorial" in name for name in support_names)
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & alpha)
    token = "bertrand_central_binom_lower_seed_candidate"
    for authority in (stable_module, alpha_enrollment_v7, editions_v7):
        assert token not in Path(authority.__file__).read_text(encoding="utf-8")


def test_helpers_and_topology_are_exact() -> None:
    left, right = _power("4", "4", "p", "left"), _power("4", "4", "p", "right")
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right and parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"p"}
    rows = _table(_specs())
    assert rows[POW_EXACT].script.count("apply pow_successor_decompose") == 2
    assert rows[POW_EXACT].script.count("apply pow_two") == 1
    assert rows[CENTRAL_EXACT].script.count("apply hrecurrence") == 4
    assert rows[CENTRAL_EXACT].script.count("apply hcentral_exists") == 4
    assert rows[CENTRAL_EXACT].script.count("apply mul_left_cancel_nonzero") == 2
    assert rows[CENTRAL_EXACT].script.count("apply PA1") == 2
    assert rows[STRICT_SEED].script[:3] == (
        "intro hrecurrence",
        "split",
        "exact central_binom_exists",
    )
    forbidden_large_literals = (str(4 * 4 * 4 * 4), str(4 * 70))
    assert not any(
        literal in row.statement
        for literal in forbidden_large_literals
        for row in rows.values()
    )


def test_receipt_manifests_are_fail_closed_and_shaped() -> None:
    for manifest in (
        EXPECTED_DEPENDENCIES,
        EXPECTED_DIRECT_CUTS,
        EXPECTED_ARTIFACTS,
        EXPECTED_BODIES,
        EXPECTED_ENVELOPES,
        EXPECTED_CLOSURES,
    ):
        assert tuple(manifest) == EXPECTED_NAMES
    assert sum(EXPECTED_DIRECT_CUTS.values()) == 10


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_artifact_receipts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256("\0".join((item.statement, *item.dependencies)).encode()).hexdigest(),
    )
    print(f"LOWER SEED ARTIFACT {name} actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, f"freeze artifact: {actual!r}"
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bodies_and_envelopes_are_frozen(name: str) -> None:
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
        label=f"lower seed body {name}",
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
    assert not any(type(node) is DNE for node in _walk(body))
    print(f"LOWER SEED BODY {name} actual={actual!r} envelope={envelope!r}", flush=True)
    assert EXPECTED_BODIES[name] is not None, f"freeze body: {actual!r}"
    assert EXPECTED_ENVELOPES[name] is not None, f"freeze envelope: {envelope!r}"
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_all_ten_direct_dependencies_are_live(name: str, dependency: str) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(dep for dep in item.dependencies if dep != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=f"({item.statement}) /\\ false"),),
            core=_row_core(name),
        )


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    rel = _relations()
    return (
        (
            POW_EXACT, "power_exponent_three", rel["power_four"],
            _power("4", "3", "p", "bpf4e_source"),
        ),
        (
            POW_EXACT, "power_base_three", rel["power_four"],
            _power("3", "4", "p", "bpf4e_source"),
        ),
        (
            CENTRAL_EXACT, "central_index_three", rel["central_four"],
            _central("3", "c", "bcb4we_source", ("c",)),
        ),
        (
            CENTRAL_EXACT,
            "weighted_compact_rhs_19",
            "4 * c = (2 * S (3 + 3)) * 20",
            "4 * c = (2 * S (3 + 3)) * 19",
        ),
        (
            STRICT_SEED, "central_index_three", rel["seed_central"],
            _central("3", "c", "bfplcb4_central", ("p", "c")),
        ),
        (
            STRICT_SEED, "power_base_five", rel["seed_power"],
            _power("5", "4", "p", "bfplcb4_power"),
        ),
        (
            STRICT_SEED, "upper_factor_three", rel["seed_result"],
            _lt("p", "3 * c", "bfplcb4_result"),
        ),
    )


def test_mutations_have_standard_counterfixtures() -> None:
    compact_power = ((4 * 4) * 4) * 4
    assert 64 != compact_power and 81 != compact_power
    assert 4 * 20 != (2 * 7) * 20
    assert 4 * 70 != (2 * 7) * 19
    assert not (compact_power < 4 * 20)
    assert not (625 < 4 * 70)
    assert not (compact_power < 3 * 70)


@pytest.mark.parametrize(("name", "case_id", "old", "new"), _mutations())
def test_genuine_mutations_are_rejected(
    name: str, case_id: str, old: str, new: str
) -> None:
    del case_id
    item = _table(_specs())[name]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_empty_context_closures_are_frozen(name: str) -> None:
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
        max_annotation_occurrences=limits.max_candidate_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_candidate_envelope_depth,
        label=f"lower seed closure {name}",
    )
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual = (
        nodes, depth, objects, edges, reused, envelope[3], envelope[4],
        _dag_hash(certificate),
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(certificate))
    direct_cut_count, probe = 0, certificate
    while type(probe) is Cut:
        direct_cut_count += 1
        probe = probe.body
    assert direct_cut_count == len(item.dependencies)
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cut_count):
        assert not check((), _corrupt_cut(certificate, index), formula)
    print(f"LOWER SEED CLOSURE {name} actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, f"freeze closure: {actual!r}"
    assert actual == EXPECTED_CLOSURES[name]
