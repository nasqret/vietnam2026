"""Fail-closed audit for the constructive large-input Bertrand theorem."""

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
from peano_lab.kernel.formulas import (
    Eq,
    Formula,
    Imp,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import (
    alpha_enrollment_v11,
    editions_v11,
    theorems as stable_module,
)
from peano_lab.library import bertrand_b7_eventual_candidate as module
from peano_lab.library.bertrand_b5_central_upper_candidate import (
    make_bertrand_b5_central_upper_candidate_theorems,
)
from peano_lab.library.bertrand_b7_eventual_candidate import (
    BERTRAND_EVENTUALLY_CLOSED_UPPER,
    make_bertrand_b7_eventual_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
)
from peano_lab.library.bertrand_primorial_choose_interval_candidate import (
    _prime_relation_term,
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

import test_bertrand_b5_central_upper_candidate as b5_harness
import test_bertrand_b6_layered_closure as b6_harness


EXPECTED_NAME = BERTRAND_EVENTUALLY_CLOSED_UPPER
EXPECTED_DEPENDENCIES = (
    "bounded_prime_interval_search",
    "le_mul_of_one_le_right",
    "le_trans",
    "lt_of_lt_of_le",
    "floor_sqrt_total",
    "division_remainder_exists",
    "central_binom_exists",
    "pow_exists",
    "four_pow_lt_mul_central_binom",
    "central_binom_le_of_no_bertrand_prime",
    "mul_le_mul_left",
    "mul_assoc",
    "bertrand_main_inequality_nat",
    "lt_not_le",
)
EXPECTED_ARTIFACT = (
    492,
    "693d9fa0c6d42e889cc22da0b6b6777e9a548242560c04c928dfb7f87b796f9c",
    "2f07009dc8e90cff5837576c54332bbd3efa57342beca46627ef5bb579769d36",
    "a3faa5bb9a173f7a7d60fe26e26ca967e58a315129dfaf7520cc3eae11430c61",
)
EXPECTED_BODY = (14, 139, 389, 77, 382, 388, 7)
EXPECTED_ENVELOPE = (389, 382, 77, 1055, 79)
EXPECTED_LAYERED = {
    "topology_sha256": (
        "9b9d4c4c0304af0c2f6b5bf4358a54895be03e9aabae6a054121cd7a6fe21cf6"
    ),
    "node_count": 413,
    "candidate_body_count": 308,
    "dependency_edge_count": 1278,
    "layer_sizes": [
        119, 82, 51, 30, 20, 14, 19, 12, 11, 8,
        8, 6, 6, 2, 1, 1, 1, 2, 2, 2,
        2, 1, 1, 1, 1, 3, 3, 2, 1, 1,
    ],
    "layer_cut_count": 30,
    "closure": [
        499202,
        181,
        37293,
        48349,
        11057,
        2227190,
        211,
        "069aa5641175a85043ab5657a3c88d4cccf645e69721bef0a5cd2610ef4dd883",
    ],
}

SOURCE_PINS = {
    "peano-lab/py/peano_lab/library/theorems.py":
        "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v11.py":
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093",
    "peano-lab/py/peano_lab/library/editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    "peano-lab/py/peano_lab/library/bertrand_prime_interval_candidate.py":
        "6b9263ffd4aa39130ff4cee9ae3f3449e4aadbc544363900f7f2289ffc701a97",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_central_binom_lower_bound_candidate.py"
    ): "60e24bb5ab7681deb6fb269033b57c74531b086e54504d5fa0239389afddaab6",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_b5_central_upper_candidate.py"
    ): "95b11876de61baa50ed1b7ff4debc2ce9afb52a35aeb2a83ff5920ca81ca77a7",
    "peano-lab/py/tests/test_bertrand_b5_central_upper_candidate.py":
        "cf2f0e7fcf1474d7623fe5c730774ea0e7f8dc93510eb0b355a85bc493de4d24",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_b6_main_inequality_candidate.py"
    ): "0b6aed58cf2865fde8e41c5d20e301169727e40599afec7ce03e0a9517d2f657",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_balanced_v1_successor_candidate.py"
    ): "852f3dc63a0bd6e80dccee70046c628e1929ae3e08bb200a016d25e1429d5b7b",
    "peano-lab/py/tests/test_bertrand_b6_layered_closure.py":
        "1b9651a9fcb0096a06b3bd1177b200c309adc48ec640bb5c2e4ebb64c97f81e6",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_b5_order_quotient_candidate.py"
    ): "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e",
    "peano-lab/py/peano_lab/library/bertrand_ceil_sqrt_candidate.py":
        "745db5174c6f9348ec97fc6076a909f1dd98e04e899e5a26ebd38b61b842b237",
    "peano-lab/py/peano_lab/library/bertrand_central_binom_candidate.py":
        "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_central_binom_prime_support_candidate.py"
    ): "d48ed42c0b5289b1565947bb43dbcbe8389eed9aa196766ff90567cfc7fec7ab",
    "peano-lab/py/peano_lab/library/bertrand_choose_foundation_candidate.py":
        "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_primorial_choose_interval_candidate.py"
    ): "5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09",
    "peano-lab/py/peano_lab/library/power_algebra_theorems.py":
        "6566c3539a18801c32d0a3ae7b6abe242bb8cf62e95184271680f0303b6fc302",
    "peano-lab/py/peano_lab/library/bertrand_b7_eventual_candidate.py":
        "6be00fab2b46ecc787b9f7f4a25f4f552a1021a20c62f5895c6047c74744d50b",
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b7-eventual-tranche-rfc-v1.md"
)
RFC_SHA256 = "d95a8224beaef6eb70443444ac7c89155bd3e1f82ce4d4751926d4d61c1545be"


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_b7_eventual_candidate_theorems(TheoremSpec)
    assert len(rows) == 1
    assert rows[0].name == EXPECTED_NAME
    return rows


def _row() -> TheoremSpec:
    return _rows()[0]


def _expected_statement() -> str:
    variables = ("n",)
    prime = "b7_prime"
    threshold = _le_term(
        "16 * 32",
        "n",
        tag="b7_threshold",
        variables=variables,
    )
    result_prime = _prime_relation_term(
        prime,
        tag="b7_result_prime",
        variables=variables + (prime,),
    )
    result_lower = _lt_term(
        "n",
        prime,
        tag="b7_result_lower",
        variables=variables + (prime,),
    )
    result_upper = _le_term(
        prime,
        "n + n",
        tag="b7_result_upper",
        variables=variables + (prime,),
    )
    result = (
        f"exists {prime}. ({result_prime}) /\\ "
        f"(({result_lower}) /\\ ({result_upper}))"
    )
    return f"forall n. ({threshold}) -> ({result})"


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    result: dict[str, TheoremSpec] = {}
    for row in editions_v11.ALPHA_SPECS:
        if row.name in stable:
            assert stable[row.name] == row
        else:
            result[row.name] = row
    for factory in b5_harness.SUPPORT_FACTORIES:
        for row in factory(TheoremSpec):
            previous = result.get(row.name)
            if previous is not None:
                assert previous == row
            elif row.name not in stable:
                result[row.name] = row
    for row in make_bertrand_b5_central_upper_candidate_theorems(TheoremSpec):
        if row.name not in stable:
            result[row.name] = row
    balanced = b6_harness._candidate_pool("bertrand_main_inequality_nat")
    for row in balanced:
        if row.name not in stable:
            result[row.name] = row
    assert EXPECTED_NAME not in result
    return result


def _core() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _candidate_base()


def _candidates() -> dict[str, TheoremSpec]:
    return _candidate_base() | _table(_rows())


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


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _core() | {item.name: item}
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


def _body_receipt() -> dict[str, object]:
    item = _row()
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
        label="B7 eventual body",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(body))
    return {
        "body": [
            len(item.dependencies),
            len(item.script),
            nodes,
            depth,
            objects,
            edges,
            reused,
        ],
        "envelope": list(envelope),
    }


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
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target)


@lru_cache(maxsize=1)
def _blueprint():
    stable = _specs_by_name()
    candidates = _candidates()
    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(current: str) -> None:
        if current in stable:
            stable_names.add(current)
            return
        item = candidates.get(current)
        assert item is not None, current
        mark = marks.get(current, 0)
        assert mark != 1
        if mark == 2:
            return
        marks[current] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[current] = 2
        candidate_order.append(current)

    visit(EXPECTED_NAME)
    names = tuple(sorted(stable_names)) + tuple(candidate_order)
    positions = {entry: index for index, entry in enumerate(names)}
    specs = {
        entry: stable[entry] if entry in stable else candidates[entry]
        for entry in names
    }
    targets = {
        entry: _closed_formula(specs[entry].statement) for entry in names
    }
    dependencies = {
        entry: ()
        if entry in stable
        else tuple(positions[item] for item in specs[entry].dependencies)
        for entry in names
    }
    topology = "\x1c".join(
        "\x1f".join(
            (
                str(positions[entry]),
                entry,
                "stable_atomic" if entry in stable else "candidate_body",
                specs[entry].statement,
                "\x1e".join(names[index] for index in dependencies[entry]),
            )
        )
        for entry in names
    )
    return (
        stable,
        candidates,
        names,
        positions,
        specs,
        targets,
        dependencies,
        sha256(topology.encode()).hexdigest(),
    )


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
        candidates,
        names,
        positions,
        specs,
        targets,
        dependencies,
        topology_sha256,
    ) = _blueprint()
    nodes: list[LayeredReplayNode] = []
    candidate_count = 0
    for entry in names:
        if entry in stable:
            theorem = replay(entry)
            assert theorem.spec == stable[entry]
            body = theorem.certificate
        else:
            candidate_count += 1
            assert candidates[entry] == specs[entry]
            body = _dependency_curried_body(specs[entry], targets)
        nodes.append(
            LayeredReplayNode(
                node_id=positions[entry],
                target=targets[entry],
                dependencies=dependencies[entry],
                body=body,
            )
        )
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    raw = LayeredReplayBundle(tuple(nodes), positions[EXPECTED_NAME])
    interned = intern_layered_replay_bodies(
        raw,
        targets[EXPECTED_NAME],
        limits=limits,
    )
    target_by_id = {node.node_id: node.target for node in interned.nodes}
    for node in interned.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(target_by_id[dependency], body_target)
        assert check((), node.body, body_target)
        assert not any(type(item) is DNE for item in _walk(node.body))
    compiled = compile_layered_replay(
        interned,
        targets[EXPECTED_NAME],
        limits=limits,
    )
    assert type(compiled) is LayeredReplayCandidate
    assert check((), compiled.certificate, compiled.target)
    assert not any(type(item) is DNE for item in _walk(compiled.certificate))
    layer_cuts = _reject_each_layer_cut(
        compiled.certificate,
        compiled.target,
    )
    assert layer_cuts == len(compiled.layers)
    return {
        "topology_sha256": topology_sha256,
        "node_count": len(names),
        "candidate_body_count": candidate_count,
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


def _run_worker(mode: str) -> dict[str, object]:
    environment = os.environ.copy()
    environment["PYTHONMALLOC"] = "malloc"
    python_root = str(Path(__file__).resolve().parents[1])
    test_root = str(Path(__file__).resolve().parent)
    inherited_path = environment.get("PYTHONPATH")
    pieces = [python_root, test_root]
    if inherited_path:
        pieces.append(inherited_path)
    environment["PYTHONPATH"] = os.pathsep.join(pieces)
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), mode],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        cwd=Path(__file__).resolve().parents[3],
    )
    assert completed.returncode == 0, (
        f"worker failed for {mode}:\n"
        f"stdout={completed.stdout[-4000:]}\n"
        f"stderr={completed.stderr[-4000:]}"
    )
    prefix = "B7EV "
    lines = [
        line for line in completed.stdout.splitlines() if line.startswith(prefix)
    ]
    assert len(lines) == 1, completed.stdout
    return json.loads(lines[0][len(prefix):])


def test_bertrand_b7_contract_statement_and_topology_are_exact() -> None:
    item = _row()
    assert item.name == EXPECTED_NAME
    assert item.statement == _expected_statement()
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert len(item.script) == 139
    parsed, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert parsed == _closed_formula(item.statement)
    assert module.__all__ == [
        "make_bertrand_b7_eventual_candidate_theorems"
    ]
    assert item.script[:8] == (
        "intro n",
        "intro hthreshold",
        next(command for command in item.script if command.startswith("have hsearch")),
        "specialize bounded_prime_interval_search n",
        "specialize bounded_prime_interval_search (n + n)",
        "exact bounded_prime_interval_search",
        "cases hsearch",
        "exact hsearch_left",
    )
    assert item.script.count("exfalso") == 1
    assert item.script.count("cases hsearch") == 1
    assert item.script.count("rewrite <- mul_assoc at hscaled_upper") == 1
    assert sum(command.startswith("rewrite") for command in item.script) == 1
    assert "exact hsearch_right" in item.script
    assert item.script[-7:] == (
        "exact hassociated_upper",
        "exact hmain",
        "specialize lt_not_le x6",
        "specialize lt_not_le (n * x3)",
        "apply lt_not_le",
        "exact hlower",
        "exact hcontradiction_upper",
    )
    assert not any(
        token in command
        for command in item.script
        for token in (
            "DNE",
            "classical",
            "sorry",
            "compact_arith",
            "by_contradiction",
            "not not",
        )
    )


def test_bertrand_b7_cutoff_and_authority_are_exact() -> None:
    source = Path(module.__file__).read_text()
    assert source.count('"16 * 32"') == 3
    assert "512" not in source
    assert "32 * 16" not in source
    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v11.ALPHA_ENTRIES}
    assert EXPECTED_NAME not in stable | alpha
    provider = "bertrand_b7_eventual_candidate"
    for authority in (stable_module, alpha_enrollment_v11, editions_v11):
        assert provider not in Path(authority.__file__).read_text()


def test_bertrand_b7_sources_and_rfc_are_pinned() -> None:
    root = Path(__file__).resolve().parents[3]
    for relative, expected in SOURCE_PINS.items():
        path = root / relative
        assert path.is_file(), relative
        assert sha256(path.read_bytes()).hexdigest() == expected
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_b7_artifact_is_frozen() -> None:
    item = _row()
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    assert actual == EXPECTED_ARTIFACT


def test_bertrand_b7_body_is_frozen() -> None:
    receipt = _run_worker("--body-worker")
    assert tuple(receipt["body"]) == EXPECTED_BODY
    assert tuple(receipt["envelope"]) == EXPECTED_ENVELOPE


@pytest.mark.parametrize("dependency", EXPECTED_DEPENDENCIES)
def test_bertrand_b7_dependencies_are_live(dependency: str) -> None:
    item = _row()
    shortened = replace(
        item,
        dependencies=tuple(
            name for name in item.dependencies if name != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_core())


def test_bertrand_b7_false_target_fails() -> None:
    item = _row()
    changed = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_core())


def _genuine_mutation() -> str:
    item = _row()
    variables = ("n", "b7_prime")
    original = _le_term(
        "b7_prime",
        "n + n",
        tag="b7_result_upper",
        variables=variables,
    )
    mutated = _le_term(
        "b7_prime",
        "n",
        tag="b7_result_upper",
        variables=variables,
    )
    assert item.statement.count(original) == 1
    return item.statement.replace(original, mutated, 1)


def test_bertrand_b7_mutation_counterfixture() -> None:
    n = 16 * 32
    assert not any(n < candidate <= n for candidate in range(n + 1))


def test_bertrand_b7_genuine_mutation_fails() -> None:
    item = _row()
    changed = replace(item, statement=_genuine_mutation())
    assert _closed_formula(changed.statement) != _closed_formula(item.statement)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=_core())


def test_bertrand_b7_layered_blueprint_is_exact() -> None:
    (
        stable,
        _,
        names,
        _,
        _,
        _,
        dependencies,
        topology_sha256,
    ) = _blueprint()
    assert len(names) == EXPECTED_LAYERED["node_count"]
    assert sum(name not in stable for name in names) == (
        EXPECTED_LAYERED["candidate_body_count"]
    )
    assert sum(map(len, dependencies.values())) == (
        EXPECTED_LAYERED["dependency_edge_count"]
    )
    assert topology_sha256 == EXPECTED_LAYERED["topology_sha256"]
    assert names[-1] == EXPECTED_NAME
    assert "central_binom_le_of_no_bertrand_prime" in names
    assert "four_pow_lt_mul_central_binom" in names
    assert "bertrand_main_inequality_nat" in names
    assert "bounded_prime_interval_search" in names


def test_bertrand_b7_layered_closure_is_frozen() -> None:
    actual = _run_worker("--closure-worker")
    assert actual == EXPECTED_LAYERED
    closure = actual["closure"]
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    assert closure[0] <= limits.max_candidate_proof_occurrences
    assert limits.max_candidate_proof_occurrences - closure[0] == 798
    assert closure[2] <= limits.max_candidate_proof_objects
    assert closure[1] <= limits.max_candidate_proof_depth
    assert closure[5] <= limits.max_candidate_annotation_occurrences
    assert closure[6] <= limits.max_candidate_envelope_depth


def _main() -> None:
    assert len(sys.argv) == 2
    mode = sys.argv[1]
    if mode == "--body-worker":
        receipt = _body_receipt()
    elif mode == "--closure-worker":
        receipt = _layered_receipt()
    else:
        raise AssertionError(mode)
    print("B7EV " + json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    _main()
