"""Focused audit for the generalized-CRT congruence foundation."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from math import gcd

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_sum_pointwise_mod_candidate import (
    make_finite_sum_pointwise_mod_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_congruence_candidate import (
    balanced_mod_eq,
    crt_solution,
    make_ha_generalized_crt_congruence_candidate_theorems,
    make_ha_generalized_crt_congruence_stack,
    promoted_mod_eq_add_cancel_left,
)
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


SUPPORT_NAME = "mod_eq_add_cancel_left"
EXPECTED_NAMES = (
    "mod_eq_zero_iff_eq",
    "mod_eq_add_cancel_right",
    "mod_eq_scale",
    "mod_eq_unscale_nonzero",
    "crt_solution_pair_congruent",
    "crt_common_solution_implies_gcd_compatible",
    "crt_incompatibility_obstructs_solution",
)
EXPECTED_STACK_NAMES = (SUPPORT_NAME, *EXPECTED_NAMES)
EXPECTED_DEPENDENCIES = {
    "mod_eq_zero_iff_eq": ("mul_zero_left",),
    "mod_eq_add_cancel_right": (SUPPORT_NAME, "add_comm"),
    "mod_eq_scale": ("mul_add", "mul_assoc"),
    "mod_eq_unscale_nonzero": (
        "mul_add",
        "mul_assoc",
        "mul_left_cancel_nonzero",
    ),
    "crt_solution_pair_congruent": ("mod_eq_symm", "mod_eq_trans"),
    "crt_common_solution_implies_gcd_compatible": (
        "is_gcd_dvd_left",
        "is_gcd_dvd_right",
        "mod_eq_of_mod_eq_multiple",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "crt_incompatibility_obstructs_solution": (
        "crt_common_solution_implies_gcd_compatible",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "mod_eq_zero_iff_eq":
        "6d14f9a6cc9886ccecbfbe1bef4976e86cae0c38764a0b06f4a8c112de9afc76",
    "mod_eq_add_cancel_right":
        "3f46c76406370d89422891af2b06373691316c78f9e45ff0126ad3e26e5becdf",
    "mod_eq_scale":
        "c72fce4853757398689509147895a6fe52f096bbb3e48c0270a66dee1377a14a",
    "mod_eq_unscale_nonzero":
        "7501e198a3840295986edf68bb81c8eaa9e4a434302cd9d7b9ac62c19f27ec29",
    "crt_solution_pair_congruent":
        "a263da6b2728d21e52c9e0721044a430faffb95d1025b266c06305da9a47cba7",
    "crt_common_solution_implies_gcd_compatible":
        "8a8bf920d82502044fdd7e18ed8c275460c55855d3e7989947ac02358d311b43",
    "crt_incompatibility_obstructs_solution":
        "194f4c29faa861337494d12f4e5064fca91cc8a21c4bdfa47560517ccc698a4d",
}
EXPECTED_BODY_RECEIPTS = {
    "mod_eq_zero_iff_eq": (1, 25, 34, 13, 34, 33, 0),
    "mod_eq_add_cancel_right": (2, 17, 22, 13, 22, 21, 0),
    "mod_eq_scale": (2, 26, 42, 21, 42, 41, 0),
    "mod_eq_unscale_nonzero": (3, 34, 49, 23, 49, 48, 0),
    "crt_solution_pair_congruent": (2, 37, 43, 18, 43, 42, 0),
    "crt_common_solution_implies_gcd_compatible": (
        5, 50, 55, 23, 55, 54, 0,
    ),
    "crt_incompatibility_obstructs_solution": (
        1, 19, 42, 26, 42, 41, 0,
    ),
}
EXPECTED_SUPPORT_BODY_RECEIPT = (2, 19, 39, 24, 39, 38, 0)
EXPECTED_CLOSED_RECEIPTS: dict[
    str, tuple[int, int, int, int, int, int, str]
] = {
    "mod_eq_add_cancel_left": (
        215, 24, 204, 214, 11, 6,
        "0f197213f155b2280177b684b0142d907b6181cdd10f0233f49bbbcb2c4323f7",
    ),
    "mod_eq_zero_iff_eq": (
        55, 13, 55, 54, 0, 1,
        "c81d939dd0cdf3b015a50b0d7ca2525670030a44bc07dcc94e53ff3c0d5dc17e",
    ),
    "mod_eq_add_cancel_right": (
        310, 25, 226, 237, 12, 8,
        "7c15168b44f390704973446c454be047adf535ff7be5703842313144a84c0ff1",
    ),
    "mod_eq_scale": (
        235, 21, 146, 158, 13, 4,
        "b8a575b14dcef4b063f1973469551f1e1d4bacf5d5e41a85f4c6f45d985735ce",
    ),
    "mod_eq_unscale_nonzero": (
        466, 26, 330, 343, 14, 11,
        "32e9b748fdce30ff2be9724b7b4c2e1831ef49abd4134958f82908ead5d3ae8e",
    ),
    "crt_solution_pair_congruent": (
        307, 31, 259, 274, 16, 8,
        "d4ea11bc6a4450bb6d3fb397defb18f8fcaa53292fcc3bbf6039a4ff9ee1ad1a",
    ),
    "crt_common_solution_implies_gcd_compatible": (
        518, 34, 388, 409, 22, 13,
        "cc5e4988e40ab3710be18c861261101d09b05604a9fb02ce9cbd583aa1c1cecc",
    ),
    "crt_incompatibility_obstructs_solution": (
        560, 35, 430, 451, 22, 14,
        "67f6acd82739752aa50cdbb33e3f02c3542d32de006ef45189f355a236b4b473",
    ),
}


@lru_cache(maxsize=1)
def _support_spec() -> TheoremSpec:
    return promoted_mod_eq_add_cancel_left(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_congruence_candidate_theorems(TheoremSpec)


def _available_specs() -> dict[str, TheoremSpec]:
    return (
        dict(_specs_by_name())
        | {_support_spec().name: _support_spec()}
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


def _cold_closed_receipts() -> dict[
    str, tuple[int, int, int, int, int, int, str]
]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    local_specs = (_support_spec(), *_candidate_specs())
    local = {item.name: item for item in local_specs}
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
    for item in (_support_spec(), *_candidate_specs()):
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique_nodes = tuple(_walk_unique(certificate))
        assert not any(type(node) is DNE for node in unique_nodes)
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        assert objects == len(unique_nodes)
        receipts[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique_nodes),
            _proof_dag_digest(certificate),
        )
    return receipts


def _mod_eq(modulus: int, left: int, right: int) -> bool:
    return left == right if modulus == 0 else left % modulus == right % modulus


def _solution(
    value: int,
    left_modulus: int,
    right_modulus: int,
    left_residue: int,
    right_residue: int,
) -> bool:
    return _mod_eq(left_modulus, value, left_residue) and _mod_eq(
        right_modulus, value, right_residue
    )


def test_generalized_crt_congruence_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_generalized_crt_congruence_candidate_theorems(TheoremSpec)
    support = _support_spec()
    original_support = make_finite_sum_pointwise_mod_candidate_theorems(
        TheoremSpec
    )[0]

    assert second == first
    assert support is not original_support
    assert support == original_support
    assert support.name == SUPPORT_NAME
    assert sha256(support.statement.encode()).hexdigest() == (
        "2dfa98ec8006d553d44bd99dabe7b140a4d391a404e6dab15e06197eb7f1e68e"
    )
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    stack = make_ha_generalized_crt_congruence_stack(TheoremSpec)
    assert stack == (support, *first)
    assert tuple(item.name for item in stack) == EXPECTED_STACK_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    assert support.name not in _specs_by_name()
    assert all(item.name not in _specs_by_name() for item in first)
    assert not hasattr(theorem_registry, "GENERALIZED_CRT_CONGRUENCE_THEOREMS")


def test_balanced_mod_eq_surface_is_parser_safe_hygienic_and_native() -> None:
    variables = ("k", "m", "a", "b")
    first = balanced_mod_eq(
        "k * m", "k * a", "k * b", tag="alpha_one", variables=variables
    )
    second = balanced_mod_eq(
        "k * m", "k * a", "k * b", tag="alpha_two", variables=variables
    )
    assert first != second
    assert parse_formula(first) == parse_formula(second)
    _, free_names = parse_formula_with_names(first)
    assert set(free_names) == set(variables)
    assert all(
        token not in first
        for token in ("ModEq(", "Congruent(", "%", "<=", "<", "-", "−")
    )

    solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="surface",
        variables=("m", "n", "a", "b", "x"),
    )
    _, solution_free = parse_formula_with_names(solution)
    assert set(solution_free) == {"m", "n", "a", "b", "x"}
    assert solution.count("exists") == 2

    with pytest.raises(ValueError, match="distinct identifiers"):
        balanced_mod_eq("m", "a", "b", tag="bad", variables=("m", "m"))
    with pytest.raises(ValueError, match="term context variable"):
        balanced_mod_eq("m", "a", "b", tag="bad", variables=("m", "a b"))
    with pytest.raises(ValueError, match="binder tag"):
        balanced_mod_eq("m", "a", "b", tag="bad tag", variables=("m", "a", "b"))
    with pytest.raises(ValueError, match="captures an argument"):
        balanced_mod_eq(
            "m",
            "a",
            "b",
            tag="capture",
            variables=("m", "a", "b", "hgcrt_mod_left_capture"),
        )
    with pytest.raises(ValueError):
        balanced_mod_eq("m", "a + z", "b", tag="unknown", variables=("m", "a", "b"))


def test_generalized_crt_contracts_are_closed_native_and_structured() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "ModEq(",
                "CRTSolution(",
                "IsGCD(",
                "Dvd(",
                "%",
                "<=",
                "<->",
            )
        )

    zero, cancel, scale, unscale, pair, necessity, obstruction = _candidate_specs()
    assert zero.statement.startswith("forall a b.")
    assert "0 * hgcrt_mod_left_zero_source" in zero.statement
    assert cancel.statement.startswith("forall d a b c.")
    assert scale.statement.startswith("forall k m a b.")
    assert "(k * m) * hgcrt_mod_left_scale_result" in scale.statement
    assert unscale.statement.startswith("forall k m a b. ~(k = 0)")
    assert pair.statement.startswith("forall m n a b x y.")
    assert necessity.statement.startswith("forall g m n a b x.")
    assert "forall hag_divisor_crt_necessity" in necessity.statement
    assert obstruction.statement.startswith("forall g m n a b.")
    assert "~(exists x." in obstruction.statement


def test_generalized_crt_bodies_are_exact_constructive_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name()) | {_support_spec().name: _support_spec()}
    support_receipt = replay_candidate_bodies(
        (_support_spec(),), core=dict(_specs_by_name())
    )[0]
    assert (
        support_receipt.dependency_count,
        support_receipt.command_count,
        support_receipt.proof_nodes,
        support_receipt.proof_depth,
        support_receipt.proof_objects,
        support_receipt.proof_edges,
        support_receipt.reused_objects,
    ) == EXPECTED_SUPPORT_BODY_RECEIPT
    receipts = replay_candidate_bodies(_candidate_specs(), core=core)
    observed = {
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
    }
    assert observed == EXPECTED_BODY_RECEIPTS

    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in commands
    )
    assert all(
        "DNE" not in command
        and "classical" not in command
        and "by_contra" not in command
        and "sorry" not in command
        for command in commands
    )

    mutations = {
        "mod_eq_zero_iff_eq": lambda statement: statement.replace(
            "-> a = b) /\\", "-> S a = b) /\\", 1
        ),
        "mod_eq_add_cancel_right": lambda statement: statement.replace(
            "= b + d * hgcrt_mod_right_right_cancel_result",
            "= S b + d * hgcrt_mod_right_right_cancel_result",
            1,
        ),
        "mod_eq_scale": lambda statement: statement.replace(
            "= (k * b) + (k * m) * hgcrt_mod_right_scale_result",
            "= S (k * b) + (k * m) * hgcrt_mod_right_scale_result",
            1,
        ),
        "mod_eq_unscale_nonzero": lambda statement: statement.replace(
            "= b + m * hgcrt_mod_right_unscale_result",
            "= S b + m * hgcrt_mod_right_unscale_result",
            1,
        ),
        "crt_solution_pair_congruent": lambda statement: statement.replace(
            "= y + n * hgcrt_mod_right_pair_mod_n",
            "= S y + n * hgcrt_mod_right_pair_mod_n",
            1,
        ),
        "crt_common_solution_implies_gcd_compatible": lambda statement: statement.replace(
            "= b + g * hgcrt_mod_right_necessity_compatibility",
            "= S b + g * hgcrt_mod_right_necessity_compatibility",
            1,
        ),
        "crt_incompatibility_obstructs_solution": lambda statement: statement.replace(
            "~(exists x.", "(exists x.", 1
        ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_generalized_crt_empty_context_closures_are_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
    assert SUPPORT_NAME not in _specs_by_name()


def test_generalized_crt_foundation_bounded_semantics() -> None:
    for a, b in product(range(7), repeat=2):
        assert _mod_eq(0, a, b) == (a == b)

    for d, a, b, c in product(range(5), repeat=4):
        if _mod_eq(d, a + c, b + c):
            assert _mod_eq(d, a, b)

    for k, m, a, b in product(range(5), repeat=4):
        if _mod_eq(m, a, b):
            assert _mod_eq(k * m, k * a, k * b)
        if k != 0 and _mod_eq(k * m, k * a, k * b):
            assert _mod_eq(m, a, b)

    for m, n, a, b, x, y in product(range(4), repeat=6):
        if _solution(x, m, n, a, b) and _solution(y, m, n, a, b):
            assert _mod_eq(m, x, y)
            assert _mod_eq(n, x, y)

    for m, n, a, b, x in product(range(5), repeat=5):
        common = gcd(m, n)
        if _solution(x, m, n, a, b):
            assert _mod_eq(common, a, b)

    for m, n, a, b in product(range(5), repeat=4):
        common = gcd(m, n)
        if not _mod_eq(common, a, b):
            assert not any(
                _solution(x, m, n, a, b) for x in range(41)
            )

    # Nearby changes are false, not merely differently formatted.
    assert _mod_eq(2, 1, 3)
    assert not _mod_eq(4, 1, 3)  # scaling only the modulus is invalid
    assert _mod_eq(1, 0, 1)
    assert 0 != 1  # modulus-one congruence cannot replace the zero convention
