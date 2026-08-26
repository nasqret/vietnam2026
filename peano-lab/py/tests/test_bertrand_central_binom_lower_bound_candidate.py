"""Fail-closed audit for the final central-binomial lower bound."""

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
    bertrand_central_binom_lower_bound_candidate as module,
    bertrand_central_binom_lower_seed_candidate as seed_module,
    bertrand_central_binom_recurrence_candidate as recurrence_module,
    bertrand_central_binom_succ_candidate as central_succ_module,
    bertrand_central_binom_zero_candidate as central_zero_module,
    bertrand_choose_diagonal_candidate as diagonal_module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_pascal_candidate as pascal_module,
    bertrand_choose_recurrence_candidate as choose_recurrence_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_symmetry_candidate as symmetry_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    bertrand_choose_weighted_vertical_candidate as weighted_module,
    bertrand_integer_envelope_candidate as integer_envelope_module,
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
from peano_lab.library.bertrand_central_binom_lower_bound_candidate import (
    make_bertrand_central_binom_lower_bound_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_lower_seed_candidate import (
    make_bertrand_central_binom_lower_seed_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_recurrence_candidate import (
    make_bertrand_central_binom_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_succ_candidate import (
    make_bertrand_central_binom_succ_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_zero_candidate import (
    make_bertrand_central_binom_zero_candidate_theorems,
)
from peano_lab.library.bertrand_choose_diagonal_candidate import (
    make_bertrand_choose_diagonal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
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


LOWER_BOUND = "four_pow_lt_mul_central_binom"
EXPECTED_NAMES = (LOWER_BOUND,)
EXPECTED_DEPENDENCIES = {
    LOWER_BOUND: (
        "lt_not_le",
        "pow_successor_decompose",
        "central_binom_succ_recurrence",
        "four_power_central_recurrence_step",
        "four_pow_central_seed_package",
    ),
}
EXPECTED_DIRECT_CUTS = {LOWER_BOUND: 5}
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    LOWER_BOUND: (
        10501,
        "8764146e7c4125f06300ff7043668e33ef417a4c15b24c5e58762c3dbb7a27f1",
        "912093bc38c0ded03fd2fa18ac2924299af829de794b718284a488cda6b0c80a",
        "f561c1eb1d627f2cdd7cd582980b5ad30c455513dabe7ab9d06b0d94668541e6",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {LOWER_BOUND: (5, 105, 276, 46, 273, 275, 3)}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    LOWER_BOUND: (276, 273, 46, 3664, 70),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    LOWER_BOUND: (
        412313,
        157,
        12961,
        13309,
        349,
        1534101,
        162,
        "c800194d88d778351aa13b5f9f0bbb42b9e7378a6f4699cc6294bf330c781b72",
    ),
}

SOURCE_PINS = {
    foundation: "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d",
    row_functional_module: (
        "dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf"
    ),
    table_functional_module: (
        "379319daec74ad2e6b89b0808f885b87f6cc1a3fab4908559511d26f51be35f5"
    ),
    laws_module: "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d",
    diagonal_module: (
        "96044d1bf4e10dfffba3f9f7482c4fd9ff1f94fffbccac9fe45af32a32a691bc"
    ),
    choose_recurrence_module: (
        "8b4a65b18e6a97a89c3f714686f2c690afb49f82ab56ed9575e3f673f50093c5"
    ),
    pascal_module: "e96ee1d140beece2666b901dc7d671743b01386f110628b0957aeff01b9c26c3",
    symmetry_module: (
        "9958068fc364ca4bd171e965283a7683d167dcd6650e7a8df13f0b27c1edb78a"
    ),
    weighted_module: (
        "e8629d085ccb2d69acb179ce2bcede5612edf290a39dac175476574f9ce76bd1"
    ),
    central_module: "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e",
    central_zero_module: (
        "978dbdbdfe2fa68a5e0db91bbf895517028c66ec5956571fd7c15d0993c52e04"
    ),
    central_succ_module: (
        "c0faea72fbe7c21ada1f15adc91dec324e0fa643bde464c9b10f9a75df4f2b27"
    ),
    integer_envelope_module: (
        "8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1"
    ),
    recurrence_module: (
        "beca6c184d6cce8eeb561134dcc95adff9c995397adccd806c3155857d372d8e"
    ),
    growth_module: "de43bd809ebd10cc31fc2ebcc12df10328e3571f491446545e34585b5a6fb66b",
    seed_module: "6bb371e4d772272a4f14937719882a61590b3ee3f1869e26ce48661115a8f1f7",
    power_algebra_module: (
        "6566c3539a18801c32d0a3ae7b6abe242bb8cf62e95184271680f0303b6fc302"
    ),
    module: "60e24bb5ab7681deb6fb269033b57c74531b086e54504d5fa0239389afddaab6",
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
    return f"exists bcf_lt_gap_{tag}. bcf_lt_gap_{tag} + S ({left}) = {right}"


def _le(left: str, right: str, tag: str) -> str:
    return f"exists bcf_le_gap_{tag}. bcf_le_gap_{tag} + ({left}) = {right}"


def _relations() -> dict[str, str]:
    variables = ("n", "p", "c")
    predecessor = "S (S (S (S n)))"
    successor = "S (S (S (S (S n))))"
    return {
        "bound": _le("4", "n", "bfplcb_bound"),
        "power": _power("4", "n", "p", "bfplcb_power"),
        "central": _central("n", "c", "bfplcb_central", variables),
        "result": _lt("p", "n * c", "bfplcb_result"),
        "package_exists": _central(
            "n", "z", "bcb4we_exists", ("n", "z")
        ),
        "package_seed_power": _power("4", "4", "p", "bfplcb4_power"),
        "package_seed_central": _central(
            "4", "c", "bfplcb4_central", ("p", "c")
        ),
        "package_seed_result": _lt("p", "4 * c", "bfplcb4_result"),
        "zero_lt_four": _lt("0", "4", "bfplcb_zero_lt_four"),
        "one_lt_four": _lt("1", "4", "bfplcb_one_lt_four"),
        "two_lt_four": _lt("2", "4", "bfplcb_two_lt_four"),
        "three_lt_four": _lt("3", "4", "bfplcb_three_lt_four"),
        "predecessor_power": _power(
            "4", predecessor, "r", "bfplcb_predecessor_power"
        ),
        "predecessor_central": _central(
            predecessor,
            "a",
            "bfplcb_predecessor_central",
            variables + ("a",),
        ),
        "predecessor_bound": _le(
            "4", predecessor, "bfplcb_predecessor_bound"
        ),
        "predecessor_result": _lt(
            "x",
            f"{predecessor} * x1",
            "bfplcb_predecessor_result",
        ),
        "successor_result": _lt(
            "x * 4", f"{successor} * c", "bfplcb_successor_result"
        ),
    }


def _expected_statement() -> str:
    rel = _relations()
    return (
        "forall n p c. "
        f"({rel['bound']}) -> ({rel['power']}) -> "
        f"({rel['central']}) -> ({rel['result']})"
    )


def _expected_script() -> tuple[str, ...]:
    rel = _relations()
    package_exists = f"forall n. exists z. ({rel['package_exists']})"
    package_seed = (
        f"forall p c. ({rel['package_seed_power']}) -> "
        f"({rel['package_seed_central']}) -> ({rel['package_seed_result']})"
    )
    predecessor = "S (S (S (S n)))"
    successor = "S (S (S (S (S n))))"
    return (
        f"have hzero_lt_four : {rel['zero_lt_four']}",
        "exists 3",
        "norm_num",
        f"have hone_lt_four : {rel['one_lt_four']}",
        "exists 2",
        "norm_num",
        f"have htwo_lt_four : {rel['two_lt_four']}",
        "exists 1",
        "norm_num",
        f"have hthree_lt_four : {rel['three_lt_four']}",
        "exists 0",
        "norm_num",
        f"have hpackage : ({package_exists}) /\\ ({package_seed})",
        "apply four_pow_central_seed_package",
        "exact central_binom_succ_recurrence",
        "cases hpackage",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "exfalso",
        "specialize lt_not_le 0",
        "specialize lt_not_le 4",
        "apply lt_not_le",
        "exact hzero_lt_four",
        "exact hbound",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "exfalso",
        "specialize lt_not_le 1",
        "specialize lt_not_le 4",
        "apply lt_not_le",
        "exact hone_lt_four",
        "exact hbound",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "exfalso",
        "specialize lt_not_le 2",
        "specialize lt_not_le 4",
        "apply lt_not_le",
        "exact htwo_lt_four",
        "exact hbound",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "exfalso",
        "specialize lt_not_le 3",
        "specialize lt_not_le 4",
        "apply lt_not_le",
        "exact hthree_lt_four",
        "exact hbound",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "apply hpackage_right",
        "exact hpower",
        "exact hcentral",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        f"have hpower_step : exists r. ({rel['predecessor_power']}) /\\ p = r * 4",
        "apply pow_successor_decompose",
        "refl",
        "exact hpower",
        "cases hpower_step",
        "cases hpower_step_witness",
        (
            "have hpredecessor_exists : exists a. "
            f"({rel['predecessor_central']})"
        ),
        "apply hpackage_left",
        "cases hpredecessor_exists",
        f"have hpredecessor_bound : {rel['predecessor_bound']}",
        "exists n",
        "simp",
        f"have hstrict : {rel['predecessor_result']}",
        "apply IH4",
        "exact hpredecessor_bound",
        "exact hpower_step_witness_left",
        "exact hpredecessor_exists_witness",
        (
            "have hrecurrence : "
            f"{successor} * c = "
            f"(2 * S ({predecessor} + {predecessor})) * x1"
        ),
        "apply central_binom_succ_recurrence",
        "exact hpredecessor_exists_witness",
        "exact hcentral",
        f"have hstep : {rel['successor_result']}",
        "apply four_power_central_recurrence_step",
        "exact hstrict",
        "exact hrecurrence",
        "rewrite hpower_step_witness_right",
        "exact hstep",
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_lower_bound_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    integer_prefix = make_bertrand_integer_envelope_candidate_theorems(
        TheoremSpec
    )[:1]
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
        *make_bertrand_central_binom_succ_candidate_theorems(TheoremSpec),
        *integer_prefix,
        *make_bertrand_central_binom_recurrence_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_candidate_theorems(TheoremSpec)[:1],
        *make_bertrand_central_binom_zero_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_lower_seed_candidate_theorems(
            TheoremSpec
        ),
    )


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    support = _table(_support_specs())
    assert not (set(public) & set(support))
    assert LOWER_BOUND not in public
    assert LOWER_BOUND not in support
    return public | support


def _row_core(name: str) -> dict[str, TheoremSpec]:
    assert name == LOWER_BOUND
    return _core()


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


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


def test_sources_surface_script_and_authority_are_exact() -> None:
    for provider, digest in SOURCE_PINS.items():
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest
    rows = _specs()
    assert make_bertrand_central_binom_lower_bound_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    item = rows[0]
    assert item.statement == _expected_statement()
    assert item.dependencies == EXPECTED_DEPENDENCIES[LOWER_BOUND]
    assert item.script == _expected_script()
    parsed, free = parse_formula_with_names(item.statement)
    assert not free and parsed == _closed_formula(item.statement)
    assert module.__all__ == [
        "make_bertrand_central_binom_lower_bound_candidate_theorems"
    ]
    assert not any(
        token in item.statement
        for token in ("Pow(", "Choose(", "CentralBinom(", "<", "^", "%")
    )
    assert not any(
        token in command
        for command in item.script
        for token in (
            "DNE", "classical", "by_contra", "sorry", "auto",
            "compact_arith", "ring", "use ",
        )
    )

    support = _table(_support_specs())
    assert len(support) == 32
    assert "central_binom_succ_recurrence" in support
    assert "four_power_central_recurrence_step" in support
    assert "four_pow_central_seed_package" in support
    assert "central_binom_exists" in support
    assert "central_binom_exists" not in item.dependencies
    for sibling in (
        "central_binom_functional",
        "central_binom_positive",
        "choose_positive",
    ):
        assert sibling not in support
    assert not any("factorial" in name for name in support)
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert LOWER_BOUND not in alpha
    token = "bertrand_central_binom_lower_bound_candidate"
    for authority in (stable_module, alpha_enrollment_v7, editions_v7):
        assert token not in Path(authority.__file__).read_text(encoding="utf-8")


def test_helpers_and_six_leaf_topology_are_exact() -> None:
    left = _central("n", "c", "left", ("n", "p", "c"))
    right = _central("n", "c", "right", ("n", "p", "c"))
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right and parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "c"}
    power_left = _power("4", "n", "p", "left")
    power_right = _power("4", "n", "p", "right")
    parsed_power_left, power_free_left = parse_formula_with_names(power_left)
    parsed_power_right, power_free_right = parse_formula_with_names(power_right)
    assert power_left != power_right
    assert parsed_power_left == parsed_power_right
    assert set(power_free_left) == set(power_free_right) == {"n", "p"}

    script = _specs()[0].script
    assert len(script) == 105
    assert script.count("induction n") == 5
    assert script.count("norm_num") == 4
    assert script.count("exfalso") == 4
    assert script.count("apply lt_not_le") == 4
    assert script.index("cases hpackage") < script.index("induction n")
    assert script.count("apply hpackage_right") == 1
    assert script.count("apply IH4") == 1
    assert not any(
        "apply IH" in command and command != "apply IH4"
        for command in script
    )
    assert script.count("apply pow_successor_decompose") == 1
    assert script.count("apply central_binom_succ_recurrence") == 1
    assert script.count("apply four_power_central_recurrence_step") == 1
    assert script[-2:] == ("rewrite hpower_step_witness_right", "exact hstep")
    assert not any(
        command.startswith("rewrite ") and command.endswith("at hpower")
        for command in script
    )
    assert not any(
        command.startswith("rewrite ") and command.endswith("at hcentral")
        for command in script
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
    assert EXPECTED_DIRECT_CUTS[LOWER_BOUND] == 5


def test_artifact_receipt_is_frozen() -> None:
    item = _specs()[0]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256("\0".join((item.statement, *item.dependencies)).encode()).hexdigest(),
    )
    print(f"CENTRAL LOWER BOUND ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[LOWER_BOUND] is not None, (
        f"freeze artifact: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[LOWER_BOUND]


def test_body_and_envelope_are_frozen() -> None:
    item = _specs()[0]
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
        label="central lower-bound body",
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
    print(
        f"CENTRAL LOWER BOUND BODY actual={actual!r} envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[LOWER_BOUND] is not None, f"freeze body: {actual!r}"
    assert EXPECTED_ENVELOPES[LOWER_BOUND] is not None, (
        f"freeze envelope: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[LOWER_BOUND]
    assert envelope == EXPECTED_ENVELOPES[LOWER_BOUND]


@pytest.mark.parametrize("dependency", EXPECTED_DEPENDENCIES[LOWER_BOUND])
def test_every_direct_dependency_is_live(dependency: str) -> None:
    item = _specs()[0]
    shortened = replace(
        item,
        dependencies=tuple(dep for dep in item.dependencies if dep != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(LOWER_BOUND))


def test_false_target_is_rejected() -> None:
    item = _specs()[0]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=f"({item.statement}) /\\ false"),),
            core=_row_core(LOWER_BOUND),
        )


def _mutations() -> tuple[tuple[str, str, str], ...]:
    rel = _relations()
    return (
        (
            "reverse_lower_bound",
            rel["bound"],
            _le("n", "4", "bfplcb_bound"),
        ),
        (
            "power_base_five",
            rel["power"],
            _power("5", "n", "p", "bfplcb_power"),
        ),
        (
            "power_successor_exponent",
            rel["power"],
            _power("4", "S n", "p", "bfplcb_power"),
        ),
        (
            "central_index_zero",
            rel["central"],
            _central("0", "c", "bfplcb_central", ("n", "p", "c")),
        ),
        (
            "upper_factor_three",
            rel["result"],
            _lt("p", "3 * c", "bfplcb_result"),
        ),
    )


def test_mutations_have_standard_counterfixtures() -> None:
    assert not (1 < 0 * 1)
    assert not (5**4 < 4 * 70)
    assert not (4**5 < 4 * 70)
    assert not (4**4 < 4 * 1)
    assert not (4**4 < 3 * 70)


@pytest.mark.parametrize(("case_id", "old", "new"), _mutations())
def test_genuine_mutations_are_rejected(
    case_id: str, old: str, new: str
) -> None:
    del case_id
    item = _specs()[0]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(LOWER_BOUND))


def test_empty_context_closure_is_frozen() -> None:
    item = _specs()[0]
    formula, certificate = _close(LOWER_BOUND)
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
        label="central lower-bound closure",
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[LOWER_BOUND]
    for index in range(direct_cut_count):
        assert not check((), _corrupt_cut(certificate, index), formula)
    print(f"CENTRAL LOWER BOUND CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[LOWER_BOUND] is not None, (
        f"freeze closure: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[LOWER_BOUND]
