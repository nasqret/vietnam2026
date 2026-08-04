"""Focused strict-HA audit for the canonical pair/cell constructor seed.

The exact theorem statements below are part of the audit.  In particular,
``pair_constructor_valid`` means D02 instantiated at the literal D01
polynomial, while ``cell_nonzero`` and ``nil_not_cell`` consume exact D06 and
D05 relation hypotheses.  No pair injectivity or list theorem is asserted.
"""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_pair_cell_seed_candidate import (
    cell,
    cell_valid,
    make_ha_pair_cell_seed_candidate_theorems,
    map_entry,
    nil_code,
    pair_code,
    pair_valid,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "pair_code_constructor",
    "pair_code_output_functional",
    "pair_constructor_valid",
    "cell_constructor",
    "cell_nonzero",
    "nil_not_cell",
    "map_entry_constructor",
)
EXPECTED_DEPENDENCIES = {
    "pair_code_constructor": (),
    "pair_code_output_functional": (),
    "pair_constructor_valid": (),
    "cell_constructor": (),
    "cell_nonzero": (),
    "nil_not_cell": ("cell_nonzero",),
    "map_entry_constructor": (),
}
EXPECTED_STATEMENTS = {
    "pair_code_constructor": (
        "forall left right. exists code. code = "
        "(left + right) * S (left + right) + (right + right)"
    ),
    "pair_code_output_functional": (
        "forall code1 code2 left right. code1 = "
        "(left + right) * S (left + right) + (right + right) -> code2 = "
        "(left + right) * S (left + right) + (right + right) -> "
        "code1 = code2"
    ),
    "pair_constructor_valid": (
        "forall left right. exists valid_left valid_right. "
        "(left + right) * S (left + right) + (right + right) = "
        "(valid_left + valid_right) * S (valid_left + valid_right) + "
        "(valid_right + valid_right)"
    ),
    "cell_constructor": (
        "forall head tail. exists code. code = S "
        "((head + tail) * S (head + tail) + (tail + tail))"
    ),
    "cell_nonzero": (
        "forall code head tail. code = S "
        "((head + tail) * S (head + tail) + (tail + tail)) -> "
        "~(code = 0)"
    ),
    "nil_not_cell": (
        "forall code head tail. code = 0 -> code = S "
        "((head + tail) * S (head + tail) + (tail + tail)) -> false"
    ),
    "map_entry_constructor": (
        "forall key value. exists entry. entry = "
        "(key + value) * S (key + value) + (value + value)"
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "pair_code_constructor":
        "f34a905487d7eb61c3515cbd0b6555f264be2a99cf9c1a17029d4a8d4a714017",
    "pair_code_output_functional":
        "4e71c8cc7a39becc48cdf6f45ffce1d33bb4996a7201f8284a6aab40420d0d0a",
    "pair_constructor_valid":
        "51e11d9dfb235d5b4e1a75bc17649746de19467e270e177fef4a2affb1d96ebd",
    "cell_constructor":
        "e4cc27df174657acfd4515daebd353cb13828be9bbb3074bc1664d0d28c3b8a1",
    "cell_nonzero":
        "1b621236aa1d6fb0f6bd24bfb10180b864ab638bf830aeb65cc4a44a372006a1",
    "nil_not_cell":
        "3f9d2ff05aaca29e9df0d9c919b41ed3614a804a8d51119d912bda99a9536629",
    "map_entry_constructor":
        "e2606d6088e4613d59bcd97835f3da3e92bfba7718a01e163740345631c5062a",
}
EXPECTED_BODY_RECEIPTS = {
    "pair_code_constructor": (0, 4, 4, 4, 4, 3, 0),
    "pair_code_output_functional": (0, 10, 10, 9, 10, 9, 0),
    "pair_constructor_valid": (0, 5, 5, 5, 5, 4, 0),
    "cell_constructor": (0, 4, 4, 4, 4, 3, 0),
    "cell_nonzero": (0, 10, 12, 9, 12, 11, 0),
    "nil_not_cell": (1, 11, 23, 15, 23, 22, 0),
    "map_entry_constructor": (0, 4, 4, 4, 4, 3, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "pair_code_constructor": (
        4, 4, 4, 3, 0, 0,
        "1682a2eb02ee68612732e527260f82758260d96df5e4d1424d0a813d8c66bd39",
    ),
    "pair_code_output_functional": (
        10, 9, 10, 9, 0, 0,
        "e2479e24af1b8b96209bcd65950895a8dcfe687a4803e8ef458f372ebed9327e",
    ),
    "pair_constructor_valid": (
        5, 5, 5, 4, 0, 0,
        "d9f2c1c74b269be3d596004f77c80adbd841bce6841d9308a398702bcfad001d",
    ),
    "cell_constructor": (
        4, 4, 4, 3, 0, 0,
        "4953e55da6c805b23447cbb1d4f1b7af5f2c42900e142d45838309ae75fae93b",
    ),
    "cell_nonzero": (
        12, 9, 12, 11, 0, 0,
        "7a0247f36cd2dffe6812b0c49c8f49e4680b59ebceff29421012e2810f150d73",
    ),
    "nil_not_cell": (
        35, 15, 35, 34, 0, 1,
        "4041048d66c132bfa7e8d6be1f58f1a5c9b1bb15a2539ad2e3a21730038d78de",
    ),
    "map_entry_constructor": (
        4, 4, 4, 3, 0, 0,
        "1682a2eb02ee68612732e527260f82758260d96df5e4d1424d0a813d8c66bd39",
    ),
}
RFC_TEMPLATES = {
    "HA-K3-PAIR-D01": (
        "code = (left + right) * S (left + right) + (right + right)"
    ),
    "HA-K3-PAIR-D02": (
        "exists left right. code = "
        "(left + right) * S (left + right) + (right + right)"
    ),
    "HA-K3-PAIR-D05": "code = 0",
    "HA-K3-PAIR-D06": (
        "code = S ((head + tail) * S (head + tail) + (tail + tail))"
    ),
    "HA-K3-PAIR-D07": (
        "exists head tail. code = S "
        "((head + tail) * S (head + tail) + (tail + tail))"
    ),
    "HA-K3-PAIR-D08": (
        "entry = (key + value) * S (key + value) + (value + value)"
    ),
}
RFC_TEMPLATE_SHA256 = {
    "HA-K3-PAIR-D01":
        "4a1f7584e17e14e5895e51feefb6083707c52d080277000a423af9edb75fc3a1",
    "HA-K3-PAIR-D02":
        "b4ccb897c33781d571f092f9fbce98963fedeab1733b7755e7622c8dcaef8bb5",
    "HA-K3-PAIR-D05":
        "90dfaef5b4215cce02fe969e7a5c252e963bd35509fc68e9116277c0928fd3d6",
    "HA-K3-PAIR-D06":
        "43b3520acd7e6b372169fe2e9636b72214359ee09c432181d38eb741ddb69e34",
    "HA-K3-PAIR-D07":
        "7313b358853482a4b4254bee45fa7bced9921cc3af56cc357eed877831e9e173",
    "HA-K3-PAIR-D08":
        "9d7cee278c784dd602f815c4feb3e3155953e91beeab3a358fbd85c6b05e1aab",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PAIR_RFC_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "arithmetic-library"
    / "ha-canonical-pair-cell-rfc-v1.md"
)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_pair_cell_seed_candidate_theorems(TheoremSpec)


def _local_specs() -> dict[str, TheoremSpec]:
    return {item.name: item for item in _candidate_specs()}


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
                (child, False) for child in children if id(child) not in digests
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
    available = dict(_specs_by_name()) | _local_specs()
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


def _cold_closed_receipts() -> dict[str, tuple[int, int, int, int, int, int, str]]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    public = _specs_by_name()
    local = _local_specs()

    @lru_cache(maxsize=None)
    def close(name: str):
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
        for dependency in item.dependencies:
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


def _pair_semantics(left: int, right: int) -> int:
    shell = left + right
    return shell * (shell + 1) + 2 * right


def _rfc_template(identifier: str) -> str:
    source = PAIR_RFC_PATH.read_text(encoding="utf-8")
    section = {
        "HA-K3-PAIR-D01": "### D01 `PairCode(code,left,right)`",
        "HA-K3-PAIR-D02": "### D02 `PairValid(code)`",
        "HA-K3-PAIR-D05": "### D05 `Nil(code)`",
        "HA-K3-PAIR-D06": "### D06 `Cell(code,head,tail)`",
        "HA-K3-PAIR-D07": "### D07 `CellValid(code)`",
        "HA-K3-PAIR-D08": "### D08 `MapEntry(entry,key,value)`",
    }[identifier]
    assert source.count(section) == 1
    suffix = source.split(section, 1)[1]
    return suffix.split("```text\n", 1)[1].split("\n```", 1)[0]


def test_pair_cell_seed_factory_is_exact_ordered_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_pair_cell_seed_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {item.name: item.statement for item in first} == EXPECTED_STATEMENTS
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_pair_cell_seed_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_pair_cell_surfaces_are_hygienic_and_match_exact_rfc_templates() -> None:
    for identifier, template in RFC_TEMPLATES.items():
        assert _rfc_template(identifier) == template
        assert sha256(template.encode()).hexdigest() == RFC_TEMPLATE_SHA256[identifier]

    assert pair_code("code", "left", "right") == RFC_TEMPLATES["HA-K3-PAIR-D01"]
    assert nil_code("code") == RFC_TEMPLATES["HA-K3-PAIR-D05"]
    assert cell("code", "head", "tail") == RFC_TEMPLATES["HA-K3-PAIR-D06"]
    assert map_entry("entry", "key", "value") == RFC_TEMPLATES["HA-K3-PAIR-D08"]

    valid_left = pair_valid("code", tag="alpha_left")
    valid_right = pair_valid("code", tag="alpha_right")
    assert valid_left != valid_right
    assert parse_formula(valid_left) == parse_formula(valid_right)
    assert parse_formula(valid_left) == parse_formula(RFC_TEMPLATES["HA-K3-PAIR-D02"])
    _, free_names = parse_formula_with_names(valid_left)
    assert set(free_names) == {"code"}

    cell_left = cell_valid("code", tag="alpha_left")
    cell_right = cell_valid("code", tag="alpha_right")
    assert cell_left != cell_right
    assert parse_formula(cell_left) == parse_formula(cell_right)
    assert parse_formula(cell_left) == parse_formula(RFC_TEMPLATES["HA-K3-PAIR-D07"])
    _, cell_free_names = parse_formula_with_names(cell_left)
    assert set(cell_free_names) == {"code"}

    with pytest.raises(ValueError, match="Peano identifier"):
        pair_code("code + 1", "left", "right")
    with pytest.raises(ValueError, match="binder tag"):
        pair_valid("code", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        pair_valid("hpc_left_capture", tag="capture")
    with pytest.raises(ValueError, match="captures an argument"):
        cell_valid("hpc_head_capture", tag="capture")


def test_pair_cell_contracts_are_closed_base_ha_formulas() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "PairCode(",
                "PairValid(",
                "Cell(",
                "Nil(",
                "MapEntry(",
                "DivRem(",
                "BetaAt(",
                "ModEq(",
                "%",
                "<",
                "<=",
            )
        )


def test_pair_cell_dependencies_are_quarantined_to_the_local_seed() -> None:
    public_closure, local_closure = _dependency_closure()
    assert public_closure == set()
    assert local_closure == {"cell_nonzero"}

    for item in _candidate_specs():
        audit_text = "\n".join(
            (item.name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_pair_cell_bodies_are_constructive_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    receipts = replay_candidate_bodies(specs)
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

    forbidden_tactics = {
        "auto",
        "compact_arith",
        "norm_num",
        "ring",
        "simp",
        "use",
    }
    commands = tuple(command for item in specs for command in item.script)
    assert all(
        command.split(maxsplit=1)[0] not in forbidden_tactics
        for command in commands
    )
    assert all(
        marker not in command.lower()
        for command in commands
        for marker in ("classical", "dne", "sorry")
    )

    mutations = {
        "pair_code_constructor": lambda statement: statement.replace(
            "+ (right + right)", "+ S (right + right)", 1
        ),
        "pair_code_output_functional": lambda statement: statement.removesuffix(
            "code1 = code2"
        ) + "code1 = S code2",
        "pair_constructor_valid": lambda statement: statement.replace(
            "+ (valid_right + valid_right)",
            "+ S (valid_right + valid_right)",
            1,
        ),
        "cell_constructor": lambda statement: statement.replace(
            "code = S ((head + tail)",
            "code = S (S ((head + tail)",
            1,
        ).replace("+ (tail + tail))", "+ (tail + tail)))", 1),
        "cell_nonzero": lambda statement: statement.replace(
            "~(code = 0)", "~(code = S 0)", 1
        ),
        "nil_not_cell": lambda statement: statement.replace(
            "code = 0 ->", "code = S 0 ->", 1
        ),
        "map_entry_constructor": lambda statement: statement.replace(
            "+ (value + value)", "+ S (value + value)", 1
        ),
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_pair_cell_bounded_semantics_and_boundary_mutations() -> None:
    observed: dict[int, tuple[int, int]] = {}
    for left in range(9):
        for right in range(9):
            code = _pair_semantics(left, right)
            assert code % 2 == 0
            assert code not in observed
            observed[code] = (left, right)

            cell_code = code + 1
            assert cell_code > 0
            assert cell_code % 2 == 1
            assert cell_code != 0

            # D08 deliberately has exactly the same one-entry constructor.
            assert _pair_semantics(left, right) == code

    assert _pair_semantics(0, 0) == 0
    assert _pair_semantics(1, 0) == 2
    assert _pair_semantics(0, 1) == 4
    assert _pair_semantics(2, 3) == 36

    # Removing the D06 successor identifies the zero/zero cell with D05 nil.
    assert _pair_semantics(0, 0) == 0
    # Removing the doubled right offset destroys injectivity inside a shell.
    shell_only = lambda left, right: (left + right) * (left + right + 1)
    assert shell_only(1, 0) == shell_only(0, 1)
    assert _pair_semantics(1, 0) != _pair_semantics(0, 1)


def test_pair_cell_empty_context_closure_is_twice_cold_and_within_limits() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()

    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)

    assert MAX_LIVE_PROOF_NODES == MAX_USE_CERTIFICATE_NODES == 500_000
    assert MAX_LIVE_PROOF_OBJECTS == MAX_USE_CERTIFICATE_OBJECTS == 100_000
    assert MAX_LIVE_PROOF_DEPTH == MAX_USE_PROOF_DEPTH == 256
    for nodes, depth, objects, _edges, _reused, _cuts, _digest in first.values():
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
        assert depth <= MAX_USE_PROOF_DEPTH
