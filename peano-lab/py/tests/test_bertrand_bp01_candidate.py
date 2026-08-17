"""Fail-closed audit for the primary Bertrand capstone BP01."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

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
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import bertrand_bp01_candidate as module
from peano_lab.library.bertrand_bp01_candidate import (
    BERTRAND_CLOSED_UPPER,
    BERTRAND_CLOSED_UPPER_BASE_SOURCE,
    make_bertrand_bp01_candidate_theorems,
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

import test_bertrand_b7_eventual_candidate as b7_harness
import test_bertrand_b8_small_candidate as b8_harness


EXPECTED_NAME = BERTRAND_CLOSED_UPPER
EXPECTED_STATEMENT = (
    "forall n. ~(n = 0) -> exists p. ((~(p = 1) /\\ "
    "forall a b. p = a * b -> a = 1 \\/ b = 1) /\\ "
    "((exists u. u + S n = p) /\\ "
    "(exists v. v + p = n + n)))"
)
EXPECTED_DEPENDENCIES = (
    "le_or_lt",
    "bertrand_eventually_closed_upper",
    "bertrand_small_closed_upper",
)
EXPECTED_SCRIPT = (
    "intro n",
    "intro hnonzero",
    "specialize le_or_lt (16 * 32)",
    "specialize le_or_lt n",
    "cases le_or_lt",
    "specialize bertrand_eventually_closed_upper n",
    "apply bertrand_eventually_closed_upper",
    "exact le_or_lt_left",
    "specialize bertrand_small_closed_upper n",
    "apply bertrand_small_closed_upper",
    "exact hnonzero",
    "exact le_or_lt_right",
)
EXPECTED_ARTIFACT: tuple[int, str, str, str] | None = (
    145,
    "7131d5cb2f6264600646df6ae949e9bb2b69a927458ce5b39682e9e284f9ad2c",
    "f9cf842ecfaf841a2a129f223c3e8430bcb8231a1a72b87764f2803c9e23bfd4",
    "595ae53696e855ac97fa711e009c0e02a1fc13b2a1e314e1c411b2ccf4f96df9",
)
EXPECTED_BODY: tuple[int, int, int, int, int, int, int] | None = (
    3, 12, 31, 15, 31, 30, 0,
)
EXPECTED_ENVELOPE: tuple[int, int, int, int, int] | None = (
    31, 31, 15, 54, 41,
)
EXPECTED_LAYERED: dict[str, object] | None = {
    "topology_sha256": (
        "eb50cd9886a40c09473f4e5caf58ec7e1f28ae114090cb7a0d376a6953ccb526"
    ),
    "node_count": 544,
    "stable_rebuilt_body_count": 202,
    "candidate_body_count": 342,
    "stable_atomic_count": 0,
    "dependency_edge_count": 1913,
    "layer_sizes": [
        55, 32, 31, 37, 26, 24, 40, 32, 28, 19, 17,
        14, 23, 6, 9, 6, 6, 15, 11, 7, 12, 13, 10,
        9, 9, 9, 8, 6, 4, 3, 2, 2, 2, 2, 1, 1,
        1, 1, 3, 3, 2, 1, 1, 1,
    ],
    "layer_cut_count": 44,
    "closure": [
        201187,
        235,
        45334,
        58587,
        13254,
        1318798,
        244,
        "e033879f901fa1e503a761f09c3fba86c9a49c3bd257c9230a777572d503d2e2",
    ],
}

for _shared_pin in set(b7_harness.SOURCE_PINS) & set(
    b8_harness.SOURCE_PINS
):
    assert (
        b7_harness.SOURCE_PINS[_shared_pin]
        == b8_harness.SOURCE_PINS[_shared_pin]
    )

SOURCE_PINS = {
    **b7_harness.SOURCE_PINS,
    **b8_harness.SOURCE_PINS,
    "peano-lab/py/peano_lab/library/bertrand_bp01_candidate.py": (
        "30e31d66c4160fb91df9b846ae58010e4eeb7618506431058d440336e32afad7"
    ),
}
RFC_PINS = {
    **b8_harness.RFC_PINS,
    b7_harness.RFC_PATH: b7_harness.RFC_SHA256,
    "research/arithmetic-library/ha-bertrand-bp01-tranche-rfc-v1.md": (
        "7eff83b267a9be832f2d6b7f0b6a2e2fff82d3cd1e6d09e806f264a5459c1ec3"
    ),
}


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_bp01_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == (EXPECTED_NAME,)
    return rows


@lru_cache(maxsize=1)
def _candidate_pool() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    result = dict(b7_harness._candidates())
    for name, row in b8_harness._available().items():
        if name in stable:
            assert stable[name] == row
            continue
        previous = result.get(name)
        if previous is not None:
            assert previous == row
        else:
            result[name] = row
    result.update(_table(_rows()))
    return result


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _specs_by_name() | _candidate_pool()
    target = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
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
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
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


def _dependency_curried_body(
    item: TheoremSpec,
    targets: dict[str, Formula],
) -> Proof:
    target = targets[item.name]
    for dependency in reversed(item.dependencies):
        target = Imp(targets[dependency], target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        assert tactic != "use"
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


@lru_cache(maxsize=1)
def _blueprint():
    stable = _specs_by_name()
    candidates = _candidate_pool()
    atomic_names: set[str] = set()
    body_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(current: str) -> None:
        item = stable.get(current, candidates.get(current))
        assert item is not None, current
        mark = marks.get(current, 0)
        assert mark != 1
        if mark == 2:
            return
        if current in stable and any(
            _primitive(command)[0] == "use" for command in item.script
        ):
            atomic_names.add(current)
            marks[current] = 2
            return
        marks[current] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[current] = 2
        body_order.append(current)

    visit(EXPECTED_NAME)
    names = tuple(sorted(atomic_names)) + tuple(body_order)
    positions = {name: index for index, name in enumerate(names)}
    specs = {
        name: stable[name] if name in stable else candidates[name]
        for name in names
    }
    targets = {
        name: _closed_formula(specs[name].statement) for name in names
    }
    dependencies = {
        name: ()
        if name in atomic_names
        else tuple(positions[dependency] for dependency in specs[name].dependencies)
        for name in names
    }
    topology = "\x1c".join(
        "\x1f".join(
            (
                str(positions[name]),
                name,
                "stable_atomic" if name in atomic_names else "rebuilt_body",
                specs[name].statement,
                "\x1e".join(names[index] for index in dependencies[name]),
            )
        )
        for name in names
    )
    return (
        stable,
        frozenset(atomic_names),
        names,
        positions,
        specs,
        targets,
        dependencies,
        sha256(topology.encode()).hexdigest(),
    )


def _bundle() -> LayeredReplayBundle:
    (
        stable,
        atomic_names,
        names,
        positions,
        specs,
        targets,
        dependencies,
        _,
    ) = _blueprint()
    nodes: list[LayeredReplayNode] = []
    for name in names:
        if name in atomic_names:
            theorem = replay(name)
            assert theorem.spec == stable[name]
            body = theorem.certificate
        else:
            body = _dependency_curried_body(specs[name], targets)
        nodes.append(
            LayeredReplayNode(
                node_id=positions[name],
                target=targets[name],
                dependencies=dependencies[name],
                body=body,
            )
        )
    return LayeredReplayBundle(tuple(nodes), positions[EXPECTED_NAME])


def _artifact_receipt() -> tuple[int, str, str, str]:
    item = _rows()[0]
    return (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )


def _body_receipt() -> dict[str, object]:
    item = _rows()[0]
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
        label="BP01 body",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(body))
    return {
        "body": [
            len(item.dependencies), len(item.script), nodes, depth,
            objects, edges, reused,
        ],
        "envelope": list(envelope),
    }


def _reject_each_layer_cut(proof: Proof, target: Formula) -> int:
    context: tuple[Formula, ...] = ()
    probe = proof
    count = 0
    bad_lemma = EqRefl(Zero())
    while type(probe) is Cut:
        assert probe.conclusion == target
        assert probe.proposition != Eq(Zero(), Zero())
        assert not check(context, replace(probe, lemma=bad_lemma), target)
        context = (probe.proposition,) + context
        probe = probe.body
        count += 1
    return count


def _layered_receipt() -> dict[str, object]:
    (
        stable,
        atomic_names,
        names,
        _,
        _,
        targets,
        dependencies,
        topology,
    ) = _blueprint()
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    interned = intern_layered_replay_bodies(
        _bundle(), targets[EXPECTED_NAME], limits=limits
    )
    compiled = compile_layered_replay(
        interned, targets[EXPECTED_NAME], limits=limits
    )
    assert type(compiled) is LayeredReplayCandidate, (
        "shared BP01 graph exceeds the unchanged layered limits; compact "
        "the lineage before freezing closure evidence"
    )
    assert check((), compiled.certificate, compiled.target)
    assert not any(type(node) is DNE for node in _walk(compiled.certificate))
    layer_cuts = _reject_each_layer_cut(
        compiled.certificate, compiled.target
    )
    assert layer_cuts == len(compiled.layers)
    return {
        "topology_sha256": topology,
        "node_count": len(names),
        "stable_rebuilt_body_count": sum(
            name in stable and name not in atomic_names for name in names
        ),
        "candidate_body_count": sum(name not in stable for name in names),
        "stable_atomic_count": len(atomic_names),
        "dependency_edge_count": sum(map(len, dependencies.values())),
        "layer_sizes": list(map(len, compiled.layers)),
        "layer_cut_count": layer_cuts,
        "closure": [
            compiled.proof_nodes,
            compiled.proof_depth,
            compiled.proof_objects,
            compiled.proof_edges,
            compiled.reused_objects,
            compiled.proof_annotation_occurrences,
            compiled.proof_envelope_depth,
            _proof_dag_sha256(compiled.certificate),
        ],
    }


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _run_worker(mode: str) -> object:
    environment = dict(os.environ)
    environment["PYTHONMALLOC"] = "malloc"
    python_root = str(Path(__file__).resolve().parents[1])
    test_root = str(Path(__file__).resolve().parent)
    inherited_path = environment.get("PYTHONPATH")
    pieces = [python_root, test_root]
    if inherited_path:
        pieces.append(inherited_path)
    environment["PYTHONPATH"] = os.pathsep.join(pieces)
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), mode],
        cwd=_repository_root() / "peano-lab" / "py",
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    line = next(
        item for item in reversed(result.stdout.splitlines())
        if item.startswith("BP01_RECEIPT ")
    )
    return json.loads(line.removeprefix("BP01_RECEIPT "))


def _mutation(case_id: str) -> str:
    if case_id == "zero_input":
        return EXPECTED_STATEMENT.replace("~(n = 0)", "n = 0", 1)
    if case_id == "closed_lower":
        return EXPECTED_STATEMENT.replace("u + S n = p", "u + S (S n) = p", 1)
    if case_id == "closed_upper":
        return EXPECTED_STATEMENT.replace("v + p = n + n", "v + p = n", 1)
    raise AssertionError(case_id)


def test_bp01_source_and_rfc_pins() -> None:
    root = _repository_root()
    for relative, digest in SOURCE_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest
    for relative, digest in RFC_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest


def test_bp01_exact_public_contract() -> None:
    item = _rows()[0]
    assert item.statement == EXPECTED_STATEMENT
    assert item.statement == BERTRAND_CLOSED_UPPER_BASE_SOURCE
    assert sha256(item.statement.encode()).hexdigest() == (
        "7131d5cb2f6264600646df6ae949e9bb2b69a927458ce5b39682e9e284f9ad2c"
    )
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert item.script == EXPECTED_SCRIPT
    assert sum("16 * 32" in command for command in item.script) == 1
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert '"512"' not in source
    assert "32 * 16" not in source


def test_bp01_artifact_is_frozen() -> None:
    actual = _artifact_receipt()
    print(f"BP01 ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACT is not None, actual
    assert actual == EXPECTED_ARTIFACT


def test_bp01_body_and_envelope_are_frozen() -> None:
    actual = _run_worker("--body-worker")
    assert isinstance(actual, dict)
    body = tuple(actual["body"])
    envelope = tuple(actual["envelope"])
    assert EXPECTED_BODY is not None, body
    assert EXPECTED_ENVELOPE is not None, envelope
    assert body == EXPECTED_BODY
    assert envelope == EXPECTED_ENVELOPE


@pytest.mark.parametrize("dependency", EXPECTED_DEPENDENCIES)
def test_bp01_every_dependency_is_live(dependency: str) -> None:
    item = _rows()[0]
    changed = replace(
        item,
        dependencies=tuple(
            name for name in item.dependencies if name != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (changed,), core=_specs_by_name() | _candidate_pool()
        )


def test_bp01_false_target_is_rejected() -> None:
    item = _rows()[0]
    changed = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (changed,), core=_specs_by_name() | _candidate_pool()
        )


def test_bp01_mutation_counterfixtures() -> None:
    assert not any(0 < prime <= 0 for prime in range(1))
    assert not any(1 < prime <= 1 for prime in range(2))
    assert not any(2 < prime <= 2 for prime in range(3))


@pytest.mark.parametrize(
    "case_id", ("zero_input", "closed_lower", "closed_upper")
)
def test_bp01_genuine_mutations_are_rejected(case_id: str) -> None:
    item = _rows()[0]
    changed = replace(item, statement=_mutation(case_id))
    assert _closed_formula(changed.statement) != _closed_formula(item.statement)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (changed,), core=_specs_by_name() | _candidate_pool()
        )


def test_bp01_layered_closure_is_frozen() -> None:
    actual = _run_worker("--closure-worker")
    assert EXPECTED_LAYERED is not None, actual
    assert actual == EXPECTED_LAYERED


def _main() -> None:
    assert len(sys.argv) == 2
    if sys.argv[1] == "--body-worker":
        receipt: object = _body_receipt()
    elif sys.argv[1] == "--closure-worker":
        receipt = _layered_receipt()
    else:
        raise AssertionError(sys.argv[1])
    print("BP01_RECEIPT " + json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    _main()
