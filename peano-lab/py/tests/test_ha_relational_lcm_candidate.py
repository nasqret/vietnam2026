"""Focused constructive audit for the isolated relational-lcm layer."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from math import lcm as natural_lcm
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_relational_lcm_candidate import (
    is_lcm,
    make_ha_relational_lcm_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


ADMITTED_NAMES = (
    "is_lcm_multiple_left",
    "is_lcm_multiple_right",
    "is_lcm_least",
    "is_lcm_symm",
    "is_lcm_unique",
    "is_lcm_zero_right",
    "is_lcm_zero_left",
)
CORE_NAMES = (
    *ADMITTED_NAMES,
    "is_lcm_of_dvd",
)
CONVENIENCE_NAMES = (
    "is_lcm_of_dvd_right",
    "product_common_multiple",
    "is_lcm_refl",
    "is_lcm_one_left",
    "is_lcm_one_right",
    "lcm_zero_left_value",
    "lcm_zero_right_value",
    "lcm_zero_left_exists_unique",
    "lcm_zero_right_exists_unique",
)
EXPECTED_NAMES = (*CORE_NAMES, *CONVENIENCE_NAMES)
RESIDUAL_PRIVATE_NAMES = ("is_lcm_of_dvd", *CONVENIENCE_NAMES)
EXPECTED_DEPENDENCIES = {
    "is_lcm_multiple_left": (),
    "is_lcm_multiple_right": (),
    "is_lcm_least": (),
    "is_lcm_symm": (),
    "is_lcm_unique": ("multiple_antisymm",),
    "is_lcm_zero_right": ("multiple_zero",),
    "is_lcm_zero_left": ("is_lcm_zero_right", "is_lcm_symm"),
    "is_lcm_of_dvd": ("multiple_refl",),
    "is_lcm_of_dvd_right": ("is_lcm_of_dvd", "is_lcm_symm"),
    "product_common_multiple": ("right_factor_divides_product",),
    "is_lcm_refl": ("multiple_refl", "is_lcm_of_dvd"),
    "is_lcm_one_left": ("one_multiple", "is_lcm_of_dvd"),
    "is_lcm_one_right": ("is_lcm_one_left", "is_lcm_symm"),
    "lcm_zero_left_value": ("is_lcm_zero_left", "is_lcm_unique"),
    "lcm_zero_right_value": ("is_lcm_zero_right", "is_lcm_unique"),
    "lcm_zero_left_exists_unique": (
        "is_lcm_zero_left",
        "is_lcm_unique",
    ),
    "lcm_zero_right_exists_unique": (
        "is_lcm_zero_right",
        "is_lcm_unique",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "is_lcm_multiple_left":
        "6bca8a86fc180bd4feba561e4808ce8fd694f687e220137f6be105ef79cf7a43",
    "is_lcm_multiple_right":
        "cfd58405c02982ebe269c680dcb0a62ac0ac33c18c8e9526046c9505f2238c61",
    "is_lcm_least":
        "7d232c7416d15f3cf128a8df8cab34ffc63e906dcc9bd0b33368b4352bd869bf",
    "is_lcm_symm":
        "e5ca139205068d953bb4d9e3c6da0c2501064201ac6ee54bd707640b7c7c30b6",
    "is_lcm_unique":
        "1e8351beb8ca8bd1ab14ce85864e37af888d97f613896316c60ba0dcbc11b48c",
    "is_lcm_zero_right":
        "a84f5e0a22729e73c1a31f5d6e2571fde1ddb828006f96db2070421d1d5e9d87",
    "is_lcm_zero_left":
        "7c6f2f252ee95f63821288659f8208bef80dc883a7927330b337e00711a2f374",
    "is_lcm_of_dvd":
        "eb81fefc899776cd175dc71a078d579174fbe5c7936b57014f1ff862da0ddc3b",
    "is_lcm_of_dvd_right":
        "e51e5862e544864a48d59d1e21d21d875476c723da77288122815a6f82d11113",
    "product_common_multiple":
        "f87e8656fc1bd22ac5bae5a740627c718db6b7940651f99c1ead6f8c0b78abea",
    "is_lcm_refl":
        "22834919e7a01e3e787607ed95a47d888f71c21820b3ff73b259a50e37d3d53a",
    "is_lcm_one_left":
        "b304968358057e53b071eeee9f4468d42388012373d4ced91254d9603bff05bb",
    "is_lcm_one_right":
        "c589196ec5efe0bfe2e2f50e6522d7dc204aa45ae809bbbf26736709592d1f46",
    "lcm_zero_left_value":
        "469b141cedd8543fc22618655f9cd83517b9bcba0df449a5bd8d8999e8dd5791",
    "lcm_zero_right_value":
        "731d9238983dc7d932e28eab75772f3d91ff1a41ad7c87d5cc3917d481f0e999",
    "lcm_zero_left_exists_unique":
        "9c134aff1a98a052cc459008668afa94d9b56c4997072385d17c43b0c25f3900",
    "lcm_zero_right_exists_unique":
        "9d17f29f58181dd887856b708e539ab3b6331603d3f28e14379613dec170f269",
}
EXPECTED_BODY_RECEIPTS = {
    "is_lcm_multiple_left": (0, 7, 21, 13, 21, 20, 0),
    "is_lcm_multiple_right": (0, 7, 21, 13, 21, 20, 0),
    "is_lcm_least": (0, 12, 24, 16, 24, 23, 0),
    "is_lcm_symm": (0, 17, 36, 21, 36, 35, 0),
    "is_lcm_unique": (1, 25, 34, 14, 34, 33, 0),
    "is_lcm_zero_right": (1, 11, 18, 7, 18, 17, 0),
    "is_lcm_zero_left": (2, 9, 10, 8, 10, 9, 0),
    "is_lcm_of_dvd": (1, 12, 16, 9, 16, 15, 0),
    "is_lcm_of_dvd_right": (2, 13, 15, 10, 15, 14, 0),
    "product_common_multiple": (1, 8, 15, 9, 15, 14, 0),
    "is_lcm_refl": (2, 8, 9, 7, 9, 8, 0),
    "is_lcm_one_left": (2, 8, 9, 7, 9, 8, 0),
    "is_lcm_one_right": (2, 9, 10, 8, 10, 9, 0),
    "lcm_zero_left_value": (2, 11, 30, 18, 30, 29, 0),
    "lcm_zero_right_value": (2, 11, 30, 18, 30, 29, 0),
    "lcm_zero_left_exists_unique": (2, 15, 37, 19, 37, 36, 0),
    "lcm_zero_right_exists_unique": (2, 15, 37, 19, 37, 36, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "is_lcm_multiple_left": (
        21, 13, 21, 20, 0, 0,
        "5c190bf7def19fc23909654cc772afcab5c479fb858898d5f143a80db366e953",
    ),
    "is_lcm_multiple_right": (
        21, 13, 21, 20, 0, 0,
        "f56c306a18651121802b73a86d0beab26f7b595bf569318f7396f3b99c76ca89",
    ),
    "is_lcm_least": (
        24, 16, 24, 23, 0, 0,
        "c1fa2a7ad9ee24262f2d1fe916db3a988dee5da6d53b067be60f378d4456f38b",
    ),
    "is_lcm_symm": (
        36, 21, 36, 35, 0, 0,
        "1651a88cf14cd0940f75b4cad21f75b4d7babd563e6df09ae54442e8fd865b43",
    ),
    "is_lcm_unique": (
        680, 34, 561, 595, 35, 19,
        "28b5d50ea9f274effaecd0ba637805b5535976124380f9647b31cab1b812dc4f",
    ),
    "is_lcm_zero_right": (
        25, 7, 25, 24, 0, 1,
        "1f46d596bf5887fb6fbbf47a571a7773c0e803a57767ddc624a016e3771d1a36",
    ),
    "is_lcm_zero_left": (
        71, 23, 71, 70, 0, 3,
        "a40c084aceae295b1af3ea106a436dfcbb2289b81387ebb03a1bc39c7676fc92",
    ),
    "is_lcm_of_dvd": (
        55, 11, 55, 54, 0, 3,
        "d1263366658d3d37613817c9bcd0e21f7180136fcfdc25d8617d7c2f548dc766",
    ),
    "is_lcm_of_dvd_right": (
        106, 23, 106, 105, 0, 5,
        "7aff4b6e58da3dda088da6ba977f0b4a1fabb50a263288635bf2ebce8e38f4b0",
    ),
    "product_common_multiple": (
        244, 26, 222, 243, 22, 8,
        "70144cd71d6b2cda4cb382dc33100c0dbc3d6242472cf18422657115473dde11",
    ),
    "is_lcm_refl": (
        103, 13, 64, 64, 1, 5,
        "9c1c7f996a39ae851114fd6191e3d4e867584ecb6b74dadf5c21e87da35944ab",
    ),
    "is_lcm_one_left": (
        96, 13, 92, 95, 4, 6,
        "734740e90689cc82db1a3aaba42eb2471229a29c80cd2b4cb7481723278d0965",
    ),
    "is_lcm_one_right": (
        142, 23, 138, 141, 4, 8,
        "90ede4dea5adabe411b2e5a81f45efcfeaca3514d229e440eb79cbbae0b523ef",
    ),
    "lcm_zero_left_value": (
        781, 36, 662, 696, 35, 24,
        "c4fb7bc6dc2d811c0a8591ee85be5d9ddcd00e67837a124b2d7baee3e4d9268f",
    ),
    "lcm_zero_right_value": (
        735, 36, 616, 650, 35, 22,
        "9e51cac408db5d62721a01bd3c71da4216f7728767d22736e05df02e3075063e",
    ),
    "lcm_zero_left_exists_unique": (
        788, 36, 669, 703, 35, 24,
        "b2ce4efd6a15d2249e224682cb8fe571f8e1cc542b1af3ebeb40ad9164eff097",
    ),
    "lcm_zero_right_exists_unique": (
        742, 36, 623, 657, 35, 22,
        "2ab337c21a1fbb5a607ad5cd9f829bed5b0ff355bf34e33dc62ee1362a06999e",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "a314f85fcee6f04ec548f7a5fd724dc67e35e514a4b79241fce4bad7b5aed318"
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc", "add_comm", "add_eq_zero_right", "add_right_cancel",
    "add_succ_left", "mul_add", "mul_assoc", "mul_comm",
    "mul_eq_one_components", "mul_eq_zero", "mul_left_cancel_nonzero",
    "mul_ne_zero", "mul_one", "mul_succ_left", "mul_zero_left",
    "multiple_antisymm", "multiple_refl", "multiple_zero", "one_mul",
    "one_multiple", "right_factor_divides_product", "succ_ne_zero",
    "zero_add", "zero_or_succ",
}
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "is_lcm_of_dvd", "is_lcm_one_left", "is_lcm_symm",
    "is_lcm_unique", "is_lcm_zero_left", "is_lcm_zero_right",
}


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_relational_lcm_candidate_theorems(TheoremSpec)


def _local_specs() -> dict[str, TheoremSpec]:
    return {item.name: item for item in _candidate_specs()}


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


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


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local_specs()


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


def _dependency_closure() -> tuple[set[str], set[str]]:
    public = _specs_by_name()
    local = _local_specs()
    pending = [
        dependency
        for item in _candidate_specs()
        for dependency in item.dependencies
    ]
    public_seen: set[str] = set()
    local_seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in public_seen or name in local_seen:
            continue
        if name in local:
            local_seen.add(name)
            pending.extend(local[name].dependencies)
        else:
            assert name in public, f"candidate dependency {name!r} is unavailable"
            public_seen.add(name)
            pending.extend(public[name].dependencies)
    return public_seen, local_seen


def _cold_closed_receipts() -> tuple[
    dict[str, tuple[int, int, int, int, int, int, str]], str
]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    public = _specs_by_name()
    local = _local_specs()

    @lru_cache(maxsize=None)
    def close(name: str):
        if name in public:
            checked = replay(name)
            return checked.formula, checked.certificate
        item = local[name]
        formula = _closed_formula(item.statement)
        target = formula
        for dependency_name in reversed(item.dependencies):
            dependency = local.get(dependency_name) or public[dependency_name]
            target = Imp(_closed_formula(dependency.statement), target)
        state = start(target)
        for dependency_name in item.dependencies:
            state = apply_tactic(state, "intro", dependency_name)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
        for dependency_name in item.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency_name in reversed(item.dependencies):
            dependency_formula, dependency_certificate = close(dependency_name)
            body = Cut(
                dependency_formula,
                formula,
                dependency_certificate,
                body,
            )
        assert check((), body, formula)
        return formula, body

    receipts = {}
    stack_records = []
    for item in _candidate_specs():
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique_nodes = tuple(_walk_unique(certificate))
        assert not any(type(node) is DNE for node in unique_nodes)
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        digest = _proof_dag_digest(certificate)
        receipts[item.name] = (
            nodes, depth, objects, edges, reused,
            sum(type(node) is Cut for node in unique_nodes), digest,
        )
        stack_records.append(f"{item.name}:{digest}")
    return receipts, sha256("\n".join(stack_records).encode()).hexdigest()


def _divides(divisor: int, value: int) -> bool:
    return value == 0 if divisor == 0 else value % divisor == 0


def _is_lcm_semantic(candidate: int, a: int, b: int) -> bool:
    if not (_divides(a, candidate) and _divides(b, candidate)):
        return False
    return all(
        not (_divides(a, common) and _divides(b, common))
        or _divides(candidate, common)
        for common in range(a * b + 1)
    )


def test_relational_lcm_factory_has_exact_public_private_boundary() -> None:
    first = _candidate_specs()
    second = make_ha_relational_lcm_candidate_theorems(TheoremSpec)
    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert tuple(item.name for item in first[:8]) == CORE_NAMES
    assert tuple(item.name for item in first[8:]) == CONVENIENCE_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    by_name = {item.name: item for item in first}
    assert all(public[name] == by_name[name] for name in ADMITTED_NAMES)
    assert all(name not in public for name in RESIDUAL_PRIVATE_NAMES)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_relational_lcm_candidate" in registry_source
    assert all(f'"{name}"' in registry_source for name in ADMITTED_NAMES)
    assert all(
        f'"{name}"' not in registry_source
        for name in RESIDUAL_PRIVATE_NAMES
    )


def test_is_lcm_surface_is_hygienic_and_accepts_only_reviewed_literals() -> None:
    alpha = is_lcm("l", "a", "b", tag="alpha")
    beta = is_lcm("l", "a", "b", tag="beta")
    assert alpha != beta
    assert parse_formula(alpha) == parse_formula(beta)
    _, free_names = parse_formula_with_names(alpha)
    assert set(free_names) == {"l", "a", "b"}

    literal = is_lcm("0", "0", "b", tag="literal")
    _, literal_free_names = parse_formula_with_names(literal)
    assert set(literal_free_names) == {"b"}
    assert is_lcm("b", "1", "b", tag="one")
    with pytest.raises(ValueError, match="Peano identifier"):
        is_lcm("2", "a", "b", tag="bad_literal")
    with pytest.raises(ValueError, match="Peano identifier"):
        is_lcm("a + 1", "a", "b", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        is_lcm("l", "a", "b", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        is_lcm("hlcm_left_factor_capture", "a", "b", tag="capture")


def test_relational_lcm_contracts_are_literal_closed_and_not_totality() -> None:
    specs = _local_specs()
    assert specs["is_lcm_zero_left"].statement == (
        f"forall b. ({is_lcm('0', '0', 'b', tag='zero_left')})"
    )
    assert specs["is_lcm_zero_right"].statement == (
        f"forall a. ({is_lcm('0', 'a', '0', tag='zero_right')})"
    )
    assert specs["is_lcm_one_left"].statement == (
        f"forall b. ({is_lcm('b', '1', 'b', tag='one_left')})"
    )
    assert specs["is_lcm_one_right"].statement == (
        f"forall a. ({is_lcm('a', 'a', '1', tag='one_right')})"
    )
    assert specs["is_lcm_zero_left"].dependencies == (
        "is_lcm_zero_right", "is_lcm_symm",
    )
    assert specs["is_lcm_zero_right"].dependencies == ("multiple_zero",)

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("IsLCM(", "Dvd(", "GCD(", "Lcm(", "%", "<=", "<")
        )
    assert "lcm_exists" not in specs
    assert not any(
        item.statement.startswith("forall a b. exists l.")
        for item in _candidate_specs()
    )


def test_relational_lcm_dependency_boundary_is_strict_constructive_ha() -> None:
    public_closure, local_closure = _dependency_closure()
    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    public = _specs_by_name()
    local = _local_specs()
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(
            marker not in audit_text
            for marker in (
                "beta", "classical", "crt", "division", "dne", "remainder",
            )
        )


def test_relational_lcm_bodies_are_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | _local_specs()
    receipts = replay_candidate_bodies(specs, core=core)
    observed = {
        receipt.name: (
            receipt.dependency_count, receipt.command_count,
            receipt.proof_nodes, receipt.proof_depth,
            receipt.proof_objects, receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    }
    assert observed == EXPECTED_BODY_RECEIPTS
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for item in specs
        for command in item.script
    )

    zero_left = _local_specs()["is_lcm_zero_left"]
    certificate, target = _body_certificate(zero_left)
    assert check((), certificate, target)
    mutation = (
        f"forall b. ({is_lcm('1', '0', 'b', tag='zero_left')})"
    )
    assert not check((), certificate, _curried_target(zero_left, mutation))


def test_relational_lcm_two_cold_closures_match_all_receipts() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == second
    assert first == (EXPECTED_CLOSED_RECEIPTS, EXPECTED_STACK_DAG_SHA256)


def test_relational_lcm_bounded_semantics_cover_edges_and_nonleast_values() -> None:
    for candidate, a, b in product(range(13), range(7), range(7)):
        assert _is_lcm_semantic(candidate, a, b) == (
            candidate == natural_lcm(a, b)
        )

    for a, b in product(range(10), repeat=2):
        assert _divides(a, a * b)
        assert _divides(b, a * b)
        assert _is_lcm_semantic(natural_lcm(a, b), a, b)

    assert _is_lcm_semantic(0, 0, 9)
    assert _is_lcm_semantic(0, 9, 0)
    assert _is_lcm_semantic(7, 1, 7)
    assert _is_lcm_semantic(7, 7, 1)
    assert _is_lcm_semantic(7, 7, 7)
    assert not _is_lcm_semantic(24, 4, 6)
