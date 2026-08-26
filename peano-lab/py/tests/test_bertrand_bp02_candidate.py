"""Fail-closed audit for the strict Bertrand capstone BP02."""

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
from peano_lab.library import bertrand_bp02_candidate as module
from peano_lab.library.bertrand_bp02_candidate import (
    BERTRAND_STRICT,
    BERTRAND_STRICT_BASE_SOURCE,
    BERTRAND_UPPER_ENDPOINT_FACTORIZATION,
    make_bertrand_bp02_candidate_theorems,
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

import test_bertrand_bp01_candidate as bp01_harness


EXPECTED_NAMES = (
    BERTRAND_UPPER_ENDPOINT_FACTORIZATION,
    BERTRAND_STRICT,
)
EXECUTION_NAMES = tuple(reversed(EXPECTED_NAMES))
EXPECTED_STATEMENTS = {
    BERTRAND_UPPER_ENDPOINT_FACTORIZATION: (
        "forall n p. "
        "(exists bpr_gap_bbp02_boundary_lower. "
        "bpr_gap_bbp02_boundary_lower + S (1) = n) -> "
        "((~(p = 1) /\\ forall bpr_left_bbp02_boundary_prime "
        "bpr_right_bbp02_boundary_prime. p = "
        "bpr_left_bbp02_boundary_prime * "
        "bpr_right_bbp02_boundary_prime -> "
        "bpr_left_bbp02_boundary_prime = 1 \\/ "
        "bpr_right_bbp02_boundary_prime = 1)) -> "
        "p = n + n -> false"
    ),
    BERTRAND_STRICT: (
        "forall n. (exists h. h + S 1 = n) -> exists p. "
        "((~(p = 1) /\\ forall a b. p = a * b -> "
        "a = 1 \\/ b = 1) /\\ ((exists u. u + S n = p) /\\ "
        "(exists v. v + S p = n + n)))"
    ),
}
EXPECTED_DEPENDENCIES = {
    BERTRAND_UPPER_ENDPOINT_FACTORIZATION: (
        "lt_not_le",
        "zero_add",
        "two_mul_eq_add_self",
        "fixed_nontrivial_factor_not_prime",
    ),
    BERTRAND_STRICT: (
        "add_eq_zero_right",
        "bertrand_closed_upper",
        "le_eq_or_lt",
        BERTRAND_UPPER_ENDPOINT_FACTORIZATION,
    ),
}
EXPECTED_DIRECT_CUTS = {
    name: len(EXPECTED_DEPENDENCIES[name]) for name in EXPECTED_NAMES
}
EXPECTED_ARTIFACTS: dict[
    str, tuple[int, str, str, str] | None
] = {
    BERTRAND_UPPER_ENDPOINT_FACTORIZATION: (
        343,
        "8e78874f3e442bf552ba3ccb16a05c561ad48986bd0d1078b16ad6be48759a6a",
        "eaaf0a7273a24fbda0564929fe0554a65d22dcfe7a6c08b977453db7aa58816d",
        "13586269c922324b50312c288b6a347cb29bee30903baf2e2f08a0aeaa680654",
    ),
    BERTRAND_STRICT: (
        162,
        "6c55889276eb7ad2577191ad7b7e46cae45a6c1437a0275db44801b54ee7ad39",
        "4f6b508a62af907403596e6452a0f857f8e3e72c1d1277e6f78e399a4814ad02",
        "7e972864c8c2a700936292f83e0ceb2633d51642f758c4898a04585e01058180",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    BERTRAND_UPPER_ENDPOINT_FACTORIZATION: (
        4, 33, 45, 18, 45, 44, 0,
    ),
    BERTRAND_STRICT: (4, 39, 51, 15, 51, 50, 0),
}
EXPECTED_ENVELOPES: dict[
    str, tuple[int, int, int, int, int] | None
] = {
    BERTRAND_UPPER_ENDPOINT_FACTORIZATION: (45, 45, 18, 22, 19),
    BERTRAND_STRICT: (51, 51, 15, 21, 18),
}
EXPECTED_LAYERED: dict[str, dict[str, object] | None] = {
    BERTRAND_UPPER_ENDPOINT_FACTORIZATION: {
        "topology_sha256": (
            "20166396c77ede95a25384cebd2d176ef9b8578769a4932a1250c2f2de5bfd5a"
        ),
        "node_count": 12,
        "stable_rebuilt_body_count": 9,
        "candidate_body_count": 3,
        "stable_atomic_count": 0,
        "dependency_edge_count": 13,
        "layer_sizes": [6, 2, 1, 1, 1, 1],
        "layer_cut_count": 6,
        "closure": [
            442,
            28,
            333,
            403,
            71,
            1022,
            29,
            "90333748033498cf8131326e2fd6cfd0eb5854d3dc187d91f3ddf8101330df33",
        ],
    },
    BERTRAND_STRICT: {
        "topology_sha256": (
            "e2543ef7fda3990a11942270cfe05eccec9dea8b94d951827bdda37e53a7519d"
        ),
        "node_count": 546,
        "stable_rebuilt_body_count": 202,
        "candidate_body_count": 344,
        "stable_atomic_count": 0,
        "dependency_edge_count": 1921,
        "layer_sizes": [
            55, 32, 31, 37, 26, 25, 40, 32, 28, 19, 17,
            14, 23, 6, 9, 6, 6, 15, 11, 7, 12, 13, 10,
            9, 9, 9, 8, 6, 4, 3, 2, 2, 2, 2, 1, 1,
            1, 1, 3, 3, 2, 1, 1, 1, 1,
        ],
        "layer_cut_count": 45,
        "closure": [
            201312,
            235,
            45408,
            58684,
            13277,
            1319167,
            244,
            "c8b5220d76d431a05b7f15ac91d1d731856e4a4ffc9eb47e80c1ed769127ee74",
        ],
    },
}

SOURCE_PINS = {
    **bp01_harness.SOURCE_PINS,
    "peano-lab/py/tests/test_bertrand_bp01_candidate.py": (
        "bea3edced4394777f2711ffb1dfbf7f6d8652e5704279b03524e9101a69a6c81"
    ),
    "peano-lab/py/peano_lab/library/bertrand_bp02_candidate.py": (
        "1bb7045f9b033e6e6167b329525d4833f66baab67bb5e846c3f572adbbb7ec0c"
    ),
}
RFC_PINS = {
    **bp01_harness.RFC_PINS,
    "research/arithmetic-library/ha-bertrand-bp02-tranche-rfc-v1.md": (
        "ef97d7b1b524e8abce6da32abf463a74cb2bc2e39f0a3334c697946bd097df80"
    ),
}


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_bp02_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


@lru_cache(maxsize=1)
def _candidate_pool() -> dict[str, TheoremSpec]:
    result = dict(bp01_harness._candidate_pool())
    result.update(_table(_rows()))
    return result


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return (
        _specs_by_name()
        | bp01_harness._candidate_pool()
        | _table(_rows()[:index])
    )


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


@lru_cache(maxsize=None)
def _blueprint(root_name: str):
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

    visit(root_name)
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
        else tuple(positions[item] for item in specs[name].dependencies)
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


def _bundle(root_name: str) -> LayeredReplayBundle:
    (
        stable,
        atomic_names,
        names,
        positions,
        specs,
        targets,
        dependencies,
        _,
    ) = _blueprint(root_name)
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
    return LayeredReplayBundle(tuple(nodes), positions[root_name])


def _artifact_receipt(name: str) -> tuple[int, str, str, str]:
    item = _table(_rows())[name]
    return (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )


def _body_receipt(name: str) -> dict[str, object]:
    item = _table(_rows())[name]
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
        label=f"BP02 body {name}",
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


def _layered_receipt(root_name: str) -> dict[str, object]:
    (
        stable,
        atomic_names,
        names,
        _,
        _,
        targets,
        dependencies,
        topology,
    ) = _blueprint(root_name)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    interned = intern_layered_replay_bodies(
        _bundle(root_name), targets[root_name], limits=limits
    )
    compiled = compile_layered_replay(
        interned, targets[root_name], limits=limits
    )
    assert type(compiled) is LayeredReplayCandidate
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


def _run_worker(mode: str, name: str) -> object:
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
        [sys.executable, str(Path(__file__).resolve()), mode, name],
        cwd=_repository_root() / "peano-lab" / "py",
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    line = next(
        item for item in reversed(result.stdout.splitlines())
        if item.startswith("BP02_RECEIPT ")
    )
    return json.loads(line.removeprefix("BP02_RECEIPT "))


def _mutations() -> dict[tuple[str, str], str]:
    boundary = EXPECTED_STATEMENTS[BERTRAND_UPPER_ENDPOINT_FACTORIZATION]
    strict = EXPECTED_STATEMENTS[BERTRAND_STRICT]
    prime_start = boundary.index("((~(p = 1)")
    prime_end = boundary.index(" -> p = n + n")
    return {
        (BERTRAND_UPPER_ENDPOINT_FACTORIZATION, "weaker_lower"):
            boundary.replace("S (1) = n", "S (0) = n", 1),
        (BERTRAND_UPPER_ENDPOINT_FACTORIZATION, "shift_endpoint"):
            boundary.replace("p = n + n", "p = S (n + n)", 1),
        (BERTRAND_UPPER_ENDPOINT_FACTORIZATION, "drop_prime"):
            boundary[:prime_start] + "p = p" + boundary[prime_end:],
        (BERTRAND_STRICT, "weaker_lower"):
            strict.replace("h + S 1 = n", "h + S 0 = n", 1),
        (BERTRAND_STRICT, "smaller_upper"):
            strict.replace("v + S p = n + n", "v + S p = n", 1),
    }


def test_bp02_source_and_rfc_pins() -> None:
    root = _repository_root()
    for relative, digest in SOURCE_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest
    for relative, digest in RFC_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest


def test_bp02_exact_contracts_and_topology() -> None:
    rows = _table(_rows())
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS.values()) == (4, 4)
    assert sum(EXPECTED_DIRECT_CUTS.values()) == 8
    for name in EXPECTED_NAMES:
        assert rows[name].statement == EXPECTED_STATEMENTS[name]
        assert rows[name].dependencies == EXPECTED_DEPENDENCIES[name]
    assert rows[BERTRAND_STRICT].statement == BERTRAND_STRICT_BASE_SOURCE
    assert sha256(rows[BERTRAND_STRICT].statement.encode()).hexdigest() == (
        "6c55889276eb7ad2577191ad7b7e46cae45a6c1437a0275db44801b54ee7ad39"
    )
    assert len(rows[BERTRAND_UPPER_ENDPOINT_FACTORIZATION].script) == 33
    assert len(rows[BERTRAND_STRICT].script) == 39
    boundary_script = rows[BERTRAND_UPPER_ENDPOINT_FACTORIZATION].script
    strict_script = rows[BERTRAND_STRICT].script
    assert not any("rewrite" in item and "hprime" in item for item in boundary_script)
    assert strict_script.count("apply bertrand_closed_upper") == 1
    assert strict_script.count("apply le_eq_or_lt") == 1
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "DNE" not in source and "classical" not in source


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_bp02_artifacts_are_frozen(name: str) -> None:
    actual = _artifact_receipt(name)
    print(f"BP02 {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_bp02_bodies_and_envelopes_are_frozen(name: str) -> None:
    actual = _run_worker("--body-worker", name)
    assert isinstance(actual, dict)
    body = tuple(actual["body"])
    envelope = tuple(actual["envelope"])
    assert EXPECTED_BODIES[name] is not None, body
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert body == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXECUTION_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == len(set(LIVE_EDGES)) == 8


@pytest.mark.parametrize(
    ("name", "dependency"),
    LIVE_EDGES,
    ids=tuple(f"{name}--{dependency}" for name, dependency in LIVE_EDGES),
)
def test_bp02_every_dependency_is_live(name: str, dependency: str) -> None:
    item = _table(_rows())[name]
    changed = replace(
        item,
        dependencies=tuple(
            value for value in item.dependencies if value != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_row_core(name))


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_bp02_false_targets_are_rejected(name: str) -> None:
    item = _table(_rows())[name]
    changed = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_row_core(name))


def test_bp02_mutation_counterfixtures() -> None:
    assert 0 < 1 and 2 == 1 + 1
    assert 1 < 2 and 5 == 2 + 2 + 1
    assert 1 < 2 and 4 == 2 + 2
    assert not any(1 < prime < 2 for prime in range(3))
    assert not any(2 < prime < 2 for prime in range(3))


@pytest.mark.parametrize(
    ("name", "case_id"),
    tuple(_mutations()),
    ids=tuple(case_id for _name, case_id in _mutations()),
)
def test_bp02_genuine_mutations_are_rejected(
    name: str,
    case_id: str,
) -> None:
    item = _table(_rows())[name]
    changed = replace(item, statement=_mutations()[(name, case_id)])
    assert _closed_formula(changed.statement) != _closed_formula(item.statement)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_row_core(name))


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_bp02_layered_closures_are_frozen(name: str) -> None:
    actual = _run_worker("--closure-worker", name)
    assert EXPECTED_LAYERED[name] is not None, actual
    assert actual == EXPECTED_LAYERED[name]


def _main() -> None:
    assert len(sys.argv) == 3
    mode, name = sys.argv[1:]
    assert name in EXPECTED_NAMES
    if mode == "--body-worker":
        receipt: object = _body_receipt(name)
    elif mode == "--closure-worker":
        receipt = _layered_receipt(name)
    else:
        raise AssertionError(mode)
    print("BP02_RECEIPT " + json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    _main()
