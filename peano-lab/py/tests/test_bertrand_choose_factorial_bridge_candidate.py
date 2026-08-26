"""Fail-closed audit for the constructive Choose-factorial bridge.

The public surface is independently expanded into raw Peano arithmetic.  Its
candidate dependency closure is rebuilt from pinned providers, with only the
diagonal-transport prefix of the symmetry package admitted.  Receipts remain
evidence and never become theorem authority.
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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import (
    alpha_enrollment_v7,
    bertrand_choose_diagonal_candidate as diagonal_module,
    bertrand_choose_factorial_bridge_candidate as module,
    bertrand_choose_factorial_support_candidate as factorial_support_module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_pascal_candidate as pascal_module,
    bertrand_choose_recurrence_candidate as recurrence_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_symmetry_candidate as symmetry_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    bertrand_choose_weighted_vertical_candidate as weighted_module,
    editions_v7,
    finite_factorial_theorems as factorial_module,
    finite_fold_surface as fold_surface,
    theorems as stable_module,
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


CHOOSE_FACTORIAL_BRIDGE = "choose_factorial_bridge"
EXPECTED_NAMES = (CHOOSE_FACTORIAL_BRIDGE,)
EXPECTED_DEPENDENCIES = {
    CHOOSE_FACTORIAL_BRIDGE: (
        "mul_one",
        "choose_exists",
        "choose_self_of_eq",
        "choose_weighted_vertical",
        "factorial_functional",
        "factorial_zero",
        "factorial_succ_decompose",
        "factorial_length_eq_transport",
        "factorial_weighted_product_combine",
    ),
}
EXPECTED_DIRECT_CUTS = {CHOOSE_FACTORIAL_BRIDGE: 9}

FOUNDATION_SOURCE_SHA256 = (
    "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
)
ROW_FUNCTIONAL_SOURCE_SHA256 = (
    "dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf"
)
TABLE_FUNCTIONAL_SOURCE_SHA256 = (
    "379319daec74ad2e6b89b0808f885b87f6cc1a3fab4908559511d26f51be35f5"
)
LAWS_SOURCE_SHA256 = (
    "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d"
)
DIAGONAL_SOURCE_SHA256 = (
    "96044d1bf4e10dfffba3f9f7482c4fd9ff1f94fffbccac9fe45af32a32a691bc"
)
RECURRENCE_SOURCE_SHA256 = (
    "8b4a65b18e6a97a89c3f714686f2c690afb49f82ab56ed9575e3f673f50093c5"
)
PASCAL_SOURCE_SHA256 = (
    "e96ee1d140beece2666b901dc7d671743b01386f110628b0957aeff01b9c26c3"
)
SYMMETRY_SOURCE_SHA256 = (
    "9958068fc364ca4bd171e965283a7683d167dcd6650e7a8df13f0b27c1edb78a"
)
WEIGHTED_SOURCE_SHA256 = (
    "e8629d085ccb2d69acb179ce2bcede5612edf290a39dac175476574f9ce76bd1"
)
FINITE_FOLD_SOURCE_SHA256 = (
    "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30"
)
FINITE_FACTORIAL_SOURCE_SHA256 = (
    "a51240629fb661c3d732cb30ad32d3fdc1d3da8b9d01f80023f12429dc7e3709"
)
FACTORIAL_SUPPORT_SOURCE_SHA256 = (
    "d9fbdfb0bf3885ac2d3245b40c680dc28ec3e838fad7fb69736a96ee2734cccc"
)
BRIDGE_SOURCE_SHA256 = (
    "22c07f0192b7e3cf6e85cb4b71fe70ecd3146c1c23cf6962ce261b369be10e09"
)

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOOSE_FACTORIAL_BRIDGE: (
        14684,
        "685e2c8461a0490ff314264f52d89cc69a76239f9a7242a7987c488552813f95",
        "8b92483f5444e79524c244fb8c41bef11965b1a7d9928abad1f0c59eecf797fe",
        "9d7765a97dc80127f89c9d59419066352814f38808909e049214586d0fadf05b",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {CHOOSE_FACTORIAL_BRIDGE: (9, 182, 257, 42, 253, 256, 4)}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOOSE_FACTORIAL_BRIDGE: (257, 253, 42, 3127, 63),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CHOOSE_FACTORIAL_BRIDGE: (
        201440,
        110,
        9406,
        9722,
        317,
        729183,
        110,
        "5257c2595f8465302c3df9b98a8292a2e7e297ef4e69ee00f7c75db36354e25f",
    ),
}


def _factorial(length: str, result: str, *, tag: str) -> str:
    """Independently reproduce the conservative factorial expansion."""

    code = f"ff_b_{tag}"
    scale = f"ff_c_{tag}"
    marker = f"ff_start_{tag}"
    range_prefix = fold_surface.range_relation(
        code,
        scale,
        marker,
        length,
        tag=f"{tag}_range",
    )
    assert range_prefix.count(marker) == 2
    range_prefix = range_prefix.replace(marker, "1")
    product = fold_surface.product_relation(
        code,
        scale,
        length,
        result,
        tag=f"{tag}_product",
    )
    return f"exists {code} {scale}. (({range_prefix}) /\\ ({product}))"


def _successor_factorial(
    predecessor: str,
    result: str,
    *,
    tag: str,
) -> str:
    marker = f"bcfb_successor_marker_{tag}"
    expanded = _factorial(marker, result, tag=tag)
    assert expanded.count(marker) == 4
    return expanded.replace(marker, f"S {predecessor}")


def _choose(
    upper: str,
    lower: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    return foundation._choose_relation_term(
        upper,
        lower,
        value,
        tag=tag,
        variables=variables,
    )


def _relations() -> dict[str, str]:
    variables = ("n", "k", "j", "c", "F", "K", "J")
    return {
        "choose": _choose(
            "n",
            "k",
            "c",
            tag="bcfb_choose",
            variables=variables,
        ),
        "total": _factorial("n", "F", tag="bcfb_total"),
        "left": _factorial("k", "K", tag="bcfb_left"),
        "right": _factorial("j", "J", tag="bcfb_right"),
        "predecessor_choose": _choose(
            "n",
            "k",
            "a",
            tag="bcfb_predecessor_choose",
            variables=variables + ("a",),
        ),
        "predecessor_total": _factorial(
            "n",
            "f",
            tag="bcfb_predecessor_total",
        ),
        "predecessor_right": _factorial(
            "j",
            "r",
            tag="bcfb_predecessor_right",
        ),
    }


def _expected_statement() -> str:
    relations = _relations()
    return (
        "forall n k j c F K J. k + j = n -> "
        f"({relations['choose']}) -> ({relations['total']}) -> "
        f"({relations['left']}) -> ({relations['right']}) -> "
        "F = (K * J) * c"
    )


def _expected_script() -> tuple[str, ...]:
    relations = _relations()
    return (
        "induction n",
        "intro k",
        "induction j",
        "intro c",
        "intro F",
        "intro K",
        "intro J",
        "intro hsum",
        "intro hchoose",
        "intro hF",
        "intro hK",
        "intro hJ",
        "have hk : k = 0",
        "trans k + 0",
        "symm",
        "apply PA3",
        "exact hsum",
        "have hc_one : c = 1",
        "specialize choose_self_of_eq 0",
        "specialize choose_self_of_eq k",
        "specialize choose_self_of_eq c",
        "apply choose_self_of_eq",
        "exact hk",
        "exact hchoose",
        "have hF_one : F = 1",
        "specialize factorial_zero 0",
        "specialize factorial_zero F",
        "apply factorial_zero",
        "refl",
        "exact hF",
        "have hK_one : K = 1",
        "specialize factorial_zero k",
        "specialize factorial_zero K",
        "apply factorial_zero",
        "exact hk",
        "exact hK",
        "have hJ_one : J = 1",
        "specialize factorial_zero 0",
        "specialize factorial_zero J",
        "apply factorial_zero",
        "refl",
        "exact hJ",
        "rewrite hF_one",
        "rewrite hK_one",
        "rewrite hJ_one",
        "rewrite hc_one",
        "specialize mul_one 1",
        "rewrite mul_one",
        "rewrite mul_one",
        "refl",
        "intro c",
        "intro F",
        "intro K",
        "intro J",
        "intro hsum",
        "rewrite PA4 at hsum",
        "exfalso",
        "apply PA1",
        "exact hsum",
        "intro k",
        "induction j",
        "intro c",
        "intro F",
        "intro K",
        "intro J",
        "intro hsum",
        "intro hchoose",
        "intro hF",
        "intro hK",
        "intro hJ",
        "have hk : k = S n",
        "trans k + 0",
        "symm",
        "apply PA3",
        "exact hsum",
        "have hc_one : c = 1",
        "specialize choose_self_of_eq (S n)",
        "specialize choose_self_of_eq k",
        "specialize choose_self_of_eq c",
        "apply choose_self_of_eq",
        "exact hk",
        "exact hchoose",
        "have hJ_one : J = 1",
        "specialize factorial_zero 0",
        "specialize factorial_zero J",
        "apply factorial_zero",
        "refl",
        "exact hJ",
        "have hFK : F = K",
        "specialize factorial_functional (S n)",
        "specialize factorial_functional F",
        "specialize factorial_functional K",
        "apply factorial_functional",
        "exact hF",
        "specialize factorial_length_eq_transport k",
        "specialize factorial_length_eq_transport (S n)",
        "specialize factorial_length_eq_transport K",
        "apply factorial_length_eq_transport",
        "exact hk",
        "exact hK",
        "rewrite hFK",
        "rewrite hJ_one",
        "rewrite hc_one",
        "specialize mul_one K",
        "rewrite mul_one",
        "rewrite mul_one",
        "refl",
        "intro c",
        "intro F",
        "intro K",
        "intro J",
        "intro hsum",
        "intro hchoose",
        "intro hF",
        "intro hK",
        "intro hJ",
        "have hprevious_sum : k + j = n",
        "apply PA2",
        "trans k + S j",
        "symm",
        "apply PA4",
        "exact hsum",
        f"have ha_exists : exists a. ({relations['predecessor_choose']})",
        "specialize choose_exists n",
        "specialize choose_exists k",
        "exact choose_exists",
        "cases ha_exists",
        "have hweighted : S j * c = S n * x",
        "specialize choose_weighted_vertical n",
        "specialize choose_weighted_vertical k",
        "specialize choose_weighted_vertical j",
        "specialize choose_weighted_vertical x",
        "specialize choose_weighted_vertical c",
        "apply choose_weighted_vertical",
        "exact hprevious_sum",
        "exact ha_exists_witness",
        "exact hchoose",
        (
            "have hF_decomp : exists f. "
            f"({relations['predecessor_total']}) /\\ F = f * S n"
        ),
        "specialize factorial_succ_decompose n",
        "specialize factorial_succ_decompose (S n)",
        "specialize factorial_succ_decompose F",
        "apply factorial_succ_decompose",
        "refl",
        "exact hF",
        "cases hF_decomp",
        "cases hF_decomp_witness",
        (
            "have hJ_decomp : exists r. "
            f"({relations['predecessor_right']}) /\\ J = r * S j"
        ),
        "specialize factorial_succ_decompose j",
        "specialize factorial_succ_decompose (S j)",
        "specialize factorial_succ_decompose J",
        "apply factorial_succ_decompose",
        "refl",
        "exact hJ",
        "cases hJ_decomp",
        "cases hJ_decomp_witness",
        "have hbridge : x1 = (K * x2) * x",
        "specialize IH k",
        "specialize IH j",
        "specialize IH x",
        "specialize IH x1",
        "specialize IH K",
        "specialize IH x2",
        "apply IH",
        "exact hprevious_sum",
        "exact ha_exists_witness",
        "exact hF_decomp_witness_left",
        "exact hK",
        "exact hJ_decomp_witness_left",
        "specialize factorial_weighted_product_combine (S j)",
        "specialize factorial_weighted_product_combine (S n)",
        "specialize factorial_weighted_product_combine x",
        "specialize factorial_weighted_product_combine c",
        "specialize factorial_weighted_product_combine x1",
        "specialize factorial_weighted_product_combine K",
        "specialize factorial_weighted_product_combine x2",
        "specialize factorial_weighted_product_combine F",
        "specialize factorial_weighted_product_combine J",
        "apply factorial_weighted_product_combine",
        "exact hJ_decomp_witness_right",
        "exact hF_decomp_witness_right",
        "exact hweighted",
        "exact hbridge",
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_factorial_bridge_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    symmetry = make_bertrand_choose_symmetry_candidate_theorems(TheoremSpec)
    assert tuple(item.name for item in symmetry[:1]) == ("choose_self_of_eq",)
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
        *symmetry[:1],
        *make_bertrand_choose_weighted_vertical_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_factorial_support_candidate_theorems(
            TheoremSpec
        ),
    )


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    support = _table(_support_specs())
    assert not (set(public) & set(support))
    assert CHOOSE_FACTORIAL_BRIDGE not in public
    assert CHOOSE_FACTORIAL_BRIDGE not in support
    assert "choose_self_of_eq" in support
    assert "choose_symmetry" not in support
    assert not any(name.startswith("central_binom_") for name in support)
    return public | support


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
            raise AssertionError("factorial bridge delegated through use")
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    public = _specs_by_name()
    if name in public:
        checked = replay(name)
        return checked.formula, checked.certificate

    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    dependencies = tuple(_close(dependency) for dependency in item.dependencies)
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


def test_choose_factorial_bridge_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (diagonal_module, DIAGONAL_SOURCE_SHA256),
        (recurrence_module, RECURRENCE_SOURCE_SHA256),
        (pascal_module, PASCAL_SOURCE_SHA256),
        (symmetry_module, SYMMETRY_SOURCE_SHA256),
        (weighted_module, WEIGHTED_SOURCE_SHA256),
        (fold_surface, FINITE_FOLD_SOURCE_SHA256),
        (factorial_module, FINITE_FACTORIAL_SOURCE_SHA256),
        (factorial_support_module, FACTORIAL_SUPPORT_SOURCE_SHA256),
        (module, BRIDGE_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_choose_factorial_bridge_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_choose_factorial_bridge_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows[0].statement == _expected_statement()
    assert rows[0].dependencies == EXPECTED_DEPENDENCIES[CHOOSE_FACTORIAL_BRIDGE]
    assert rows[0].script == _expected_script()
    assert module.__all__ == [
        "make_bertrand_choose_factorial_bridge_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert CHOOSE_FACTORIAL_BRIDGE not in stable
    assert CHOOSE_FACTORIAL_BRIDGE not in alpha
    assert set(rows[0].dependencies) <= set(_core())

    provider_token = "bertrand_choose_factorial_bridge_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    formula, free_names = parse_formula_with_names(rows[0].statement)
    assert not free_names
    assert formula == _closed_formula(rows[0].statement)
    for token in (
        "Choose(",
        "Factorial(",
        "Product(",
        "Range(",
        "<=",
        "<",
        "^",
        "%",
        "|",
    ):
        assert token not in rows[0].statement
    for command in rows[0].script:
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


def test_choose_factorial_bridge_script_topology_is_exact() -> None:
    script = _specs()[0].script
    assert script == _expected_script()
    assert script.count("induction n") == 1
    assert script.count("induction j") == 2
    assert not any(command == "induction k" for command in script)
    assert script.count("apply PA1") == 1
    assert script.count("apply choose_self_of_eq") == 2
    assert script.count("exact choose_exists") == 1
    assert script.count("apply choose_weighted_vertical") == 1
    assert script.count("apply factorial_functional") == 1
    assert script.count("apply factorial_zero") == 4
    assert script.count("apply factorial_succ_decompose") == 2
    assert script.count("apply factorial_length_eq_transport") == 1
    assert script.count("apply factorial_weighted_product_combine") == 1
    assert script.count("rewrite mul_one") == 4
    assert script.count("cases ha_exists") == 1
    assert script.count("cases hF_decomp") == 1
    assert script.count("cases hF_decomp_witness") == 1
    assert script.count("cases hJ_decomp") == 1
    assert script.count("cases hJ_decomp_witness") == 1
    assert not any(
        command.startswith("rewrite ")
        and command.endswith((" at hchoose", " at hF", " at hK", " at hJ"))
        for command in script
    )


def test_choose_factorial_bridge_helpers_are_hygienic() -> None:
    relations = _relations()
    expected_free = {
        "choose": {"n", "k", "c"},
        "total": {"n", "F"},
        "left": {"k", "K"},
        "right": {"j", "J"},
    }
    for key, names in expected_free.items():
        _formula, free = parse_formula_with_names(relations[key])
        assert set(free) == names

    left = _factorial("n", "F", tag="bridge_hygiene_left")
    right = _factorial("n", "F", tag="bridge_hygiene_right")
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "F"}
    assert factorial_module.factorial_relation(
        "n", "F", tag="bridge_hygiene_left"
    ) == left

    successor = _successor_factorial(
        "n",
        "F",
        tag="bridge_hygiene_successor",
    )
    _successor_formula, successor_free = parse_formula_with_names(successor)
    assert set(successor_free) == {"n", "F"}
    with pytest.raises(ValueError):
        factorial_module.factorial_relation(
            "ff_i_valid_range", "F", tag="valid"
        )
    with pytest.raises(ValueError):
        factorial_module.factorial_relation("n", "F", tag="bad tag")

    variables = ("n", "k", "c")
    choose_left = _choose(
        "n", "k", "c", tag="bridge_choose_left", variables=variables
    )
    choose_right = _choose(
        "n", "k", "c", tag="bridge_choose_right", variables=variables
    )
    parsed_choose_left, free_choose_left = parse_formula_with_names(choose_left)
    parsed_choose_right, free_choose_right = parse_formula_with_names(
        choose_right
    )
    assert choose_left != choose_right
    assert parsed_choose_left == parsed_choose_right
    assert set(free_choose_left) == set(free_choose_right) == set(variables)
    with pytest.raises(ValueError):
        _choose(
            "n",
            "k",
            "c",
            tag="valid",
            variables=variables + ("bcf_row_code_valid",),
        )
    with pytest.raises(ValueError):
        _choose(
            "n", "k", "c", tag="bad tag", variables=variables
        )


def test_choose_factorial_bridge_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


def test_choose_factorial_bridge_artifact_is_frozen() -> None:
    item = _specs()[0]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE FACTORIAL BRIDGE ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[CHOOSE_FACTORIAL_BRIDGE] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[CHOOSE_FACTORIAL_BRIDGE]


def test_choose_factorial_bridge_body_is_frozen() -> None:
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
        label="choose factorial bridge body",
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
        f"CHOOSE FACTORIAL BRIDGE BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[CHOOSE_FACTORIAL_BRIDGE] is not None, (
        f"freeze body receipt: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[CHOOSE_FACTORIAL_BRIDGE] is not None, (
        f"freeze envelope receipt: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[CHOOSE_FACTORIAL_BRIDGE]
    assert envelope == EXPECTED_ENVELOPES[CHOOSE_FACTORIAL_BRIDGE]


@pytest.mark.parametrize(
    "dependency",
    EXPECTED_DEPENDENCIES[CHOOSE_FACTORIAL_BRIDGE],
)
def test_choose_factorial_bridge_every_dependency_is_live(
    dependency: str,
) -> None:
    item = _specs()[0]
    shortened = replace(
        item,
        dependencies=tuple(
            candidate
            for candidate in item.dependencies
            if candidate != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_core())


def test_choose_factorial_bridge_false_target_is_rejected() -> None:
    item = _specs()[0]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_core())


def _mutations() -> tuple[tuple[str, str, str], ...]:
    relations = _relations()
    variables = ("n", "k", "j", "c", "F", "K", "J")
    choose_upper = _choose(
        "S n",
        "k",
        "c",
        tag="bcfb_choose",
        variables=variables,
    )
    choose_column = _choose(
        "n",
        "S k",
        "c",
        tag="bcfb_choose",
        variables=variables,
    )
    total_successor = _successor_factorial(
        "n",
        "F",
        tag="bcfb_total",
    )
    left_successor = _successor_factorial(
        "k",
        "K",
        tag="bcfb_left",
    )
    right_successor = _successor_factorial(
        "j",
        "J",
        tag="bcfb_right",
    )
    return (
        ("shift_complement", "k + j = n", "k + j = S n"),
        ("shift_choose_row", relations["choose"], choose_upper),
        ("shift_choose_column", relations["choose"], choose_column),
        ("shift_total_factorial", relations["total"], total_successor),
        ("shift_left_factorial", relations["left"], left_successor),
        ("shift_right_factorial", relations["right"], right_successor),
        ("drop_choose_factor", "F = (K * J) * c", "F = K * J"),
        (
            "successor_result",
            "F = (K * J) * c",
            "F = S ((K * J) * c)",
        ),
    )


def test_choose_factorial_bridge_mutations_have_counterfixtures() -> None:
    assert 1 != 2  # shifted complement at (n,k,j,c,F,K,J)=(1,0,2,1,1,1,2)
    assert 1 != 2  # shifted Choose row at (1,1,0,2,1,1,1)
    assert 2 != 4  # shifted Choose column at (2,0,2,2,2,1,2)
    assert 2 != 1  # shifted total factorial at (1,1,0,1,2,1,1)
    assert 2 != 4  # shifted left factorial at (2,1,1,2,2,2,1)
    assert 2 != 4  # shifted right factorial at (2,1,1,2,2,1,2)
    assert 2 != 1  # dropping c at (2,1,1,2,2,1,1)
    assert 1 != 2  # successor result at the all-zero indices


@pytest.mark.parametrize(
    ("case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[0] for case in _mutations()),
)
def test_choose_factorial_bridge_genuine_mutations_are_rejected(
    case_id: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = _specs()[0]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_core())


def test_choose_factorial_bridge_closure_is_frozen() -> None:
    item = _specs()[0]
    formula, certificate = _close(CHOOSE_FACTORIAL_BRIDGE)
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
        label="choose factorial bridge closure",
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[CHOOSE_FACTORIAL_BRIDGE]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    print(f"CHOOSE FACTORIAL BRIDGE CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[CHOOSE_FACTORIAL_BRIDGE] is not None, (
        f"freeze independent closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[CHOOSE_FACTORIAL_BRIDGE]
