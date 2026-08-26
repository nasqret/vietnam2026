"""Focused audit for the constructive generalized-CRT sufficiency ladder."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from math import gcd, lcm

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_generalized_crt_congruence_candidate import (
    make_ha_generalized_crt_congruence_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_sufficiency_candidate import (
    make_ha_generalized_crt_sufficiency_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "factor_nonzero_right",
    "is_gcd_quotients_coprime_nonzero",
    "is_gcd_nonzero_coprime_quotients",
    "mod_eq_common_remainder_decomposition",
    "crt_scaled_common_remainder_lift",
    "generalized_binary_crt_sufficient_nonzero",
    "generalized_binary_crt_solvable_iff_nonzero",
)
ADMITTED_NAMES = (
    "is_gcd_quotients_coprime_nonzero",
    "mod_eq_common_remainder_decomposition",
    "crt_scaled_common_remainder_lift",
    "generalized_binary_crt_sufficient_nonzero",
)
RESIDUAL_PRIVATE_NAMES = (
    "factor_nonzero_right",
    "is_gcd_nonzero_coprime_quotients",
    "generalized_binary_crt_solvable_iff_nonzero",
)
EXPECTED_DEPENDENCIES = {
    "factor_nonzero_right": ("factor_nonzero_left", "mul_comm"),
    "is_gcd_quotients_coprime_nonzero": (
        "is_gcd_greatest",
        "mul_assoc",
        "mul_one",
        "mul_left_cancel_nonzero",
        "divisor_one",
    ),
    "is_gcd_nonzero_coprime_quotients": (
        "is_gcd_dvd_left",
        "is_gcd_dvd_right",
        "factor_nonzero_left",
        "factor_nonzero_right",
        "is_gcd_quotients_coprime_nonzero",
    ),
    "mod_eq_common_remainder_decomposition": (
        "division_remainder_exists",
        "remainder_decomposition_to_mod_eq",
        "mod_eq_symm",
        "mod_eq_trans",
        "mod_eq_to_remainder_decomposition",
        "mul_comm",
    ),
    "crt_scaled_common_remainder_lift": (
        "binary_crt",
        "mod_eq_scale",
        "mod_eq_refl",
        "mod_eq_add",
    ),
    "generalized_binary_crt_sufficient_nonzero": (
        "is_gcd_dvd_left",
        "is_gcd_dvd_right",
        "mul_zero_left",
        "is_gcd_quotients_coprime_nonzero",
        "mod_eq_common_remainder_decomposition",
        "crt_scaled_common_remainder_lift",
    ),
    "generalized_binary_crt_solvable_iff_nonzero": (
        "crt_common_solution_implies_gcd_compatible",
        "generalized_binary_crt_sufficient_nonzero",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "factor_nonzero_right":
        "543c8a224463c4a8e9b804003a71339b81c2ac631239343247d440de245dd7f1",
    "is_gcd_quotients_coprime_nonzero":
        "0bc474f2b82d5fef83c2a189e481247157c496bcb2736b26b1afdf8cac046be3",
    "is_gcd_nonzero_coprime_quotients":
        "983a20f87e6ca944f17cebdc5b5c9a602c61e060f6bf6132a7af602860da6116",
    "mod_eq_common_remainder_decomposition":
        "cdb6b4faa868300dad212c67261e39297413f0aaa63cdaaee262ef9c5974776b",
    "crt_scaled_common_remainder_lift":
        "c95894cec0533133e6e90e6e3dec521cebec2addeec0af5641b0840c0f94c8e1",
    "generalized_binary_crt_sufficient_nonzero":
        "beb4079f3e85fbe8451677090e362d1d9c063361c021ca42a45b242789904b33",
    "generalized_binary_crt_solvable_iff_nonzero":
        "6739df870ea7c5edf490ed06ce73ebfc46df694441bdabbd69ed1edde526f286",
}
EXPECTED_SCRIPT_REPR_SHA256 = {
    "factor_nonzero_right":
        "c1b3942f05df1ad83938d12decfa1523d6d460d7a2ba2dcc12a71cd228be53a7",
    "is_gcd_quotients_coprime_nonzero":
        "74c663896bc42ccf73b1439d13b9e347cd1547f77b1be1e44886d607a02df26d",
    "is_gcd_nonzero_coprime_quotients":
        "79e7ca6e7bae407741154a6a6c49bec5c911c83da9de4df0b458faf997a09b80",
    "mod_eq_common_remainder_decomposition":
        "a758dd823aba7aa620e36ee2ef5770097fa7398dc21e75bf121117f9bc72e874",
    "crt_scaled_common_remainder_lift":
        "50a328f159622418fdfe1f04fc4a8be096804c7f5e913bb54b0c137e17f6ca59",
    "generalized_binary_crt_sufficient_nonzero":
        "f6c366bf9dda9b44fd296cb7a8af5c8cb2717765ccd5d433bffd214a274791f4",
    "generalized_binary_crt_solvable_iff_nonzero":
        "6e0a69794e1b2025d6079d097b22cbc1028923ed7ceef93b58a3ac096d6697c7",
}
EXPECTED_BODY_RECEIPTS = {
    "factor_nonzero_right": (2, 15, 31, 20, 31, 30, 0),
    "is_gcd_quotients_coprime_nonzero": (5, 61, 75, 30, 75, 74, 0),
    "is_gcd_nonzero_coprime_quotients": (5, 71, 91, 29, 90, 90, 1),
    "mod_eq_common_remainder_decomposition": (6, 61, 73, 24, 73, 72, 0),
    "crt_scaled_common_remainder_lift": (4, 78, 91, 35, 91, 90, 0),
    "generalized_binary_crt_sufficient_nonzero": (6, 85, 120, 38, 119, 119, 1),
    "generalized_binary_crt_solvable_iff_nonzero": (2, 31, 73, 28, 73, 72, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "factor_nonzero_right": (
        290, 26, 247, 269, 23, 9, 0,
        "fa36c22be01d8493018a0a520e57b4d55bb6a49606ca66b593d627a3bca93e3c",
    ),
    "is_gcd_quotients_coprime_nonzero": (
        660, 33, 562, 595, 34, 18, 0,
        "b20e99453775b46993595aa0c53a4e8facc56e037ef7d138d3005098d1bf973d",
    ),
    "is_gcd_nonzero_coprime_quotients": (
        1120, 38, 876, 931, 56, 32, 0,
        "bac838b1489a5285b36e24d437fb4cb5f5f452d31cb3340b9f88818ee05fb8a2",
    ),
    "mod_eq_common_remainder_decomposition": (
        2894, 69, 1075, 1138, 64, 43, 0,
        "7615686f1fb9c23b0b53a4cc46a1da5349bd6fd6b808d8ef0203b45a213fd6fc",
    ),
    "crt_scaled_common_remainder_lift": (
        5745, 52, 2062, 2174, 113, 92, 0,
        "188a46f051c74f8a3f53c3945a3760fff3be12df5d89c2b468e94cf201166674",
    ),
    "generalized_binary_crt_sufficient_nonzero": (
        9482, 74, 3147, 3302, 156, 141, 0,
        "9c1ad09a4bfb2ee8e273320069d6ef6f9e50c0229aa023bb45cf887ddd9c2a1b",
    ),
    "generalized_binary_crt_solvable_iff_nonzero": (
        10073, 76, 3316, 3476, 161, 149, 0,
        "8956a66d8f72d512f840464d2749e43258a2b74b3828dde58f2c206d53af0234",
    ),
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_congruence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_sufficiency_candidate_theorems(TheoremSpec)


def _assert_public_private_boundary() -> None:
    reviewed = {item.name: item for item in _candidate_specs()}
    assert set(reviewed) == set(ADMITTED_NAMES) | set(RESIDUAL_PRIVATE_NAMES)
    assert set(ADMITTED_NAMES).isdisjoint(RESIDUAL_PRIVATE_NAMES)
    public = _specs_by_name()
    admitted = tuple(
        item
        for item in theorem_registry.HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS
        if item.name in ADMITTED_NAMES
    )

    assert admitted == tuple(reviewed[name] for name in ADMITTED_NAMES)
    assert all(public[name] == reviewed[name] for name in ADMITTED_NAMES)
    assert all(name not in public for name in RESIDUAL_PRIVATE_NAMES)
    assert all(
        name not in {item.name for item in admitted}
        for name in RESIDUAL_PRIVATE_NAMES
    )


def _available_specs() -> dict[str, TheoremSpec]:
    return (
        dict(_specs_by_name())
        | {item.name: item for item in _prior_specs()}
        | {item.name: item for item in _candidate_specs()}
    )


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
    yield proof
    for child in _proof_children(proof):
        yield from _walk(child)


def _walk_unique(proof: Proof):
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


def _proof_dag_digest(proof: Proof) -> str:
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


def _curried_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency_name].statement), target)
    return target


def _body_certificate(item: TheoremSpec):
    target = _curried_target(item)
    state = start(target)
    for dependency_name in item.dependencies:
        state = apply_tactic(state, "intro", dependency_name)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _cold_closed_receipts():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    local = {
        item.name: item for item in (*_prior_specs(), *_candidate_specs())
    }
    public = _specs_by_name()

    @lru_cache(maxsize=None)
    def close(name: str):
        if name in public:
            checked = replay(name)
            return checked.formula, checked.certificate

        item = local[name]
        formula = _closed_formula(item.statement)
        dependency_specs = tuple(
            local.get(dependency) or public[dependency]
            for dependency in item.dependencies
        )
        target = formula
        for dependency_spec in reversed(dependency_specs):
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in item.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
        for _dependency in item.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(item.dependencies):
            dependency_formula, dependency_certificate = close(dependency)
            body = Cut(
                dependency_formula,
                formula,
                dependency_certificate,
                body,
            )
        assert check((), body, formula)
        return formula, body

    receipts = {}
    for item in _candidate_specs():
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique_nodes = tuple(_walk_unique(certificate))
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        receipts[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique_nodes),
            sum(type(node) is DNE for node in unique_nodes),
            _proof_dag_digest(certificate),
        )
    return receipts


def test_sufficiency_factory_has_exact_public_private_boundary() -> None:
    first = _candidate_specs()
    second = make_ha_generalized_crt_sufficiency_candidate_theorems(TheoremSpec)
    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    assert {
        item.name: sha256(repr(item.script).encode()).hexdigest() for item in first
    } == EXPECTED_SCRIPT_REPR_SHA256
    _assert_public_private_boundary()


def test_sufficiency_contracts_are_closed_native_and_bounded() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert len(item.statement) < 4000
        assert all(
            token not in item.statement
            for token in (
                "IsGCD(",
                "Coprime(",
                "ModEq(",
                "CRTSolution(",
                "Dvd(",
                "%",
                "<=",
                "<->",
            )
        )

    assert _candidate_specs()[0].statement.endswith("~(d = 0)")
    assert "exists M N." in _candidate_specs()[2].statement
    assert "exists A B r." in _candidate_specs()[3].statement
    assert _candidate_specs()[5].statement.startswith("forall g m n a b.")
    assert "/\\" in _candidate_specs()[6].statement


def test_sufficiency_bodies_are_constructive_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item for item in _prior_specs()
    }
    receipts = replay_candidate_bodies(_candidate_specs(), core=core)
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == EXPECTED_BODY_RECEIPTS

    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "classical", "by_contra", "sorry")
    )

    mutations = {
        "factor_nonzero_right": lambda s: s.replace("~(d = 0)", "~(c = 0)", 1),
        "is_gcd_quotients_coprime_nonzero": lambda s: s.replace(
            "m = g * M", "m = g * S M", 1
        ),
        "is_gcd_nonzero_coprime_quotients": lambda s: s.replace(
            "n = g * N", "n = g * S N", 1
        ),
        "mod_eq_common_remainder_decomposition": lambda s: s.replace(
            "b = g * B + r", "b = g * B + S r", 1
        ),
        "crt_scaled_common_remainder_lift": lambda s: s.replace(
            "a = g * A + r", "a = g * A + S r", 1
        ),
        "generalized_binary_crt_sufficient_nonzero": lambda s: s.replace(
            "~(m = 0)", "~(S m = 0)", 1
        ),
        "generalized_binary_crt_solvable_iff_nonzero": lambda s: s.replace(
            "~(n = 0)", "~(S n = 0)", 1
        ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_sufficiency_empty_context_closures_are_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    _assert_public_private_boundary()


def test_sufficiency_bounded_semantics() -> None:
    for c, d in product(range(6), repeat=2):
        if c * d != 0:
            assert d != 0

    for m, n in product(range(1, 8), repeat=2):
        g = gcd(m, n)
        left = m // g
        right = n // g
        assert g != 0 and left != 0 and right != 0
        assert gcd(left, right) == 1

    for g, a, b in product(range(1, 6), range(8), range(8)):
        if a % g == b % g:
            remainder = a % g
            assert a == g * (a // g) + remainder
            assert b == g * (b // g) + remainder
            assert remainder < g

    for m, n, a, b in product(range(1, 6), range(1, 6), range(6), range(6)):
        compatible = a % gcd(m, n) == b % gcd(m, n)
        solutions = [
            x for x in range(lcm(m, n))
            if x % m == a % m and x % n == b % n
        ]
        assert bool(solutions) == compatible
