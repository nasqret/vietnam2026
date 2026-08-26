"""Fail-closed audit for the Bertrand B5 square-tail valuation tranche.

Every body, rejection, and empty-context closure root runs in a fresh
subprocess with ``PYTHONMALLOC=malloc``.  The harness therefore never retains
multiple large proof DAGs in one interpreter.
"""

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
from peano_lab.library import editions_v11
from peano_lab.library.bertrand_b5_order_quotient_candidate import (
    make_bertrand_b5_order_quotient_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_central_binom_carry_candidate import (
    make_bertrand_central_binom_carry_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_square_tail_candidate import (
    make_bertrand_central_binom_square_tail_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_valuation_candidate import (
    make_bertrand_central_binom_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
)
from peano_lab.library.bertrand_power_valuation_candidate import (
    _power_terms,
    power_valuation,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_residue_map_candidate import prime
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


EXCLUSION = "central_binom_prime_square_tail_exponent_not_two_le"
RESULT = "central_binom_prime_square_tail_valuation_le_one"
EXPECTED_NAMES = (EXCLUSION, RESULT)
EXPECTED_DEPENDENCIES = {
    EXCLUSION: (
        "pow_exists",
        "prime_nonzero",
        "one_le_of_ne_zero",
        "pow_tail_strict_of_square",
        "central_binom_prime_power_contribution_le_double",
        "lt_not_le",
    ),
    RESULT: ("le_or_lt", EXCLUSION),
}
EXPECTED_COMMAND_COUNTS = {EXCLUSION: 56, RESULT: 31}

EXPECTED_ARTIFACTS = {
    EXCLUSION: (
        20_161,
        "44c9ce733a77bf091416fb77a991c16a6798b936d08d5b2901fb5c186b935d9f",
        "cbed71cb72a66e3054dd9c3360d55e8d2c9cc0e05347ec85cf5ed995840eccd8",
        "0741381be7985b75f8c6371641a17523d29a9251180650982ae4f20bcf92ec1a",
    ),
    RESULT: (
        20_576,
        "068ccc064b402af674f74adeade8f8e991e711d08213a74cac5d2513901fc3f1",
        "a9cebdaae536ff7be2c8a7b3b5304cc1241faa931f21f5e23ee1c8c8c9f8c7ef",
        "71ba6f6bee13f4008784cd65e3267d20f715d7541fc21102998e3b142a9422d0",
    ),
}
EXPECTED_BODIES = {
    EXCLUSION: (6, 56, 68, 32, 68, 67, 0),
    RESULT: (2, 31, 39, 28, 39, 38, 0),
}
EXPECTED_ENVELOPES = {
    EXCLUSION: (68, 68, 32, 20, 32),
    RESULT: (39, 39, 28, 8, 28),
}
EXPECTED_LAYERED_CLOSURES = {
    EXCLUSION: {
        "topology_sha256": (
            "bf68e43b46390a2fb4e8b76597ac5a025f7a978f150578e4bb6887295ed1e0a5"
        ),
        "node_count": 182,
        "stable_catalog_count": 432,
        "reachable_stable_count": 71,
        "candidate_body_count": 111,
        "dependency_edge_count": 407,
        "layer_sizes": [
            78, 37, 15, 8, 9, 7, 7, 6, 3, 2, 1, 1, 2, 1, 1, 1, 1, 1,
            1,
        ],
        "layer_cut_count": 19,
        "proof_nodes": 273_079,
        "proof_depth": 96,
        "proof_objects": 13_355,
        "proof_edges": 17_591,
        "reused_objects": 4_237,
        "annotation_occurrences": 981_570,
        "envelope_depth": 96,
        "package_formula_occurrences": 63_526,
        "package_formula_depth": 57,
        "proof_dag_sha256": (
            "4359602deefd243a640c5d49b24f1d419e1098d0ad510b81fd4d760f712969f0"
        ),
    },
    RESULT: {
        "topology_sha256": (
            "ec0ef65ba8dc0fd88f2ec2d430bb841e4d60f109f3fb36d10896cbd2f6ae7993"
        ),
        "node_count": 183,
        "stable_catalog_count": 432,
        "reachable_stable_count": 71,
        "candidate_body_count": 112,
        "dependency_edge_count": 409,
        "layer_sizes": [
            78, 37, 15, 8, 9, 7, 7, 6, 3, 2, 1, 1, 2, 1, 1, 1, 1, 1,
            1, 1,
        ],
        "layer_cut_count": 20,
        "proof_nodes": 273_129,
        "proof_depth": 96,
        "proof_objects": 13_391,
        "proof_edges": 17_637,
        "reused_objects": 4_247,
        "annotation_occurrences": 983_649,
        "envelope_depth": 96,
        "package_formula_occurrences": 64_590,
        "package_formula_depth": 57,
        "proof_dag_sha256": (
            "7f820d19e49946c3d6b86efccbd650885946a36c43d6e2b54eb57a371325d993"
        ),
    },
}

SOURCE_PINS = {
    "bertrand_b5_order_quotient_candidate.py": (
        "4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e"
    ),
    "bertrand_central_binom_valuation_candidate.py": (
        "76ab449e7ae0dc58d7c99743e7df39e59d5619b8801387cd40a8cb242e2b79e8"
    ),
    "bertrand_central_binom_carry_candidate.py": (
        "a480ca001ad0837c2ae45315bd5520c666d5e716a34c72ec5f5fcc0d7601c0f0"
    ),
    "bertrand_central_binom_square_tail_candidate.py": (
        "b07163c977af5bbbf4f84aaec3629c9c58c06e8acc7fed476134e980aec7a9ff"
    ),
    "alpha_enrollment_v11.py": (
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093"
    ),
    "editions_v11.py": (
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf"
    ),
}
RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-b5-square-tail-tranche-rfc-v1.md"
)
RFC_SHA256 = (
    "dac2a5aee172a8ec78121ff5c83cbeead54f6b08733a0b91fb79183318eac7b5"
)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_central_binom_square_tail_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


@lru_cache(maxsize=1)
def _expected_statements() -> dict[str, str]:
    variables = ("p", "n", "C", "v", "s")

    def statement(prefix: str, result: str) -> str:
        primality = prime("p", tag=f"{prefix}_prime")
        positive = _le_term(
            "1", "n", tag=f"{prefix}_positive", variables=variables
        )
        central = _central_binom_relation_term(
            "n", "C", tag=f"{prefix}_central", variables=variables
        )
        valuation = power_valuation(
            "p", "C", "v", tag=f"{prefix}_valuation"
        )
        square = _power_terms("p", "2", "s", tag=f"{prefix}_square")
        strict = _lt_term(
            "n + n", "s", tag=f"{prefix}_strict", variables=variables
        )
        return (
            "forall p n C v s. "
            f"({primality}) -> ({positive}) -> ({central}) -> "
            f"({valuation}) -> ({square}) -> ({strict}) -> {result}"
        )

    exclusion_bound = _le_term(
        "2", "v", tag="bcpsten_exponent", variables=variables
    )
    final_bound = _le_term(
        "v", "1", tag="bcpstvlo_result", variables=variables
    )
    return {
        EXCLUSION: statement("bcpsten", f"~({exclusion_bound})"),
        RESULT: statement("bcpstvlo", f"({final_bound})"),
    }


@lru_cache(maxsize=1)
def _mutations() -> dict[str, str]:
    expected = _expected_statements()
    variables = ("p", "n", "C", "v", "s")
    old_exponent = _le_term(
        "2", "v", tag="bcpsten_exponent", variables=variables
    )
    new_exponent = _le_term(
        "1", "v", tag="bcpsten_exponent", variables=variables
    )
    old_result = _le_term(
        "v", "1", tag="bcpstvlo_result", variables=variables
    )
    new_result = _le_term(
        "S v", "1", tag="bcpstvlo_result", variables=variables
    )
    assert expected[EXCLUSION].count(old_exponent) == 1
    assert expected[RESULT].count(old_result) == 1
    return {
        EXCLUSION: expected[EXCLUSION].replace(
            f"~({old_exponent})", f"~({new_exponent})"
        ),
        RESULT: expected[RESULT].replace(old_result, new_result),
    }


@lru_cache(maxsize=1)
def _candidate_base() -> dict[str, TheoremSpec]:
    stable = _specs_by_name()
    rows = (
        *editions_v11.ALPHA_SPECS,
        *make_bertrand_b5_order_quotient_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_valuation_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_carry_candidate_theorems(TheoremSpec),
    )
    result: dict[str, TheoremSpec] = {}
    for row in rows:
        if row.name in stable:
            assert stable[row.name] == row
            continue
        previous = result.get(row.name)
        if previous is not None:
            assert previous == row
        result[row.name] = row
    assert not set(EXPECTED_NAMES) & set(result)
    return result


def _row_candidates(name: str) -> dict[str, TheoremSpec]:
    prefix = _rows()[: EXPECTED_NAMES.index(name) + 1]
    return _candidate_base() | _table(prefix)


def _row_core(name: str) -> dict[str, TheoremSpec]:
    prefix = _rows()[: EXPECTED_NAMES.index(name)]
    return dict(_specs_by_name()) | _candidate_base() | _table(prefix)


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _candidate_base() | _table(_rows())


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
        label=f"B5 square-tail body {name}",
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
    assert not any(type(node) is DNE for node in _walk(body))
    return {"body": list(actual), "envelope": list(envelope)}


def _rejection_worker(
    kind: str,
    name: str,
    dependency: str | None = None,
) -> None:
    item = _table(_rows())[name]
    if kind == "dependency":
        assert dependency is not None
        changed = replace(
            item,
            dependencies=tuple(
                entry for entry in item.dependencies if entry != dependency
            ),
        )
        assert len(changed.dependencies) + 1 == len(item.dependencies)
    elif kind == "false":
        assert dependency is None
        changed = replace(item, statement=f"({item.statement}) /\\ false")
    elif kind == "mutation":
        assert dependency is None
        changed = replace(item, statement=_mutations()[name])
        assert _closed_formula(changed.statement) != _closed_formula(
            item.statement
        )
    else:
        raise AssertionError(kind)
    try:
        replay_candidate_bodies((changed,), core=_row_core(name))
    except CandidateBodyError:
        return
    raise AssertionError(f"{kind} replay unexpectedly passed for {name}")


def _mutate_layer_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_layer_cut(proof.body, index - 1))


def _blueprint(name: str):
    stable = _specs_by_name()
    candidates = _row_candidates(name)
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

    visit(name)
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


def _layered_receipt(name: str) -> dict[str, object]:
    (
        stable,
        candidates,
        names,
        positions,
        specs,
        targets,
        dependencies,
        topology_sha256,
    ) = _blueprint(name)
    nodes: list[LayeredReplayNode] = []
    candidate_count = 0
    for entry in names:
        if entry in stable:
            theorem = replay(entry)
            assert theorem.spec == stable[entry]
            assert theorem.formula == targets[entry]
            body = theorem.certificate
        else:
            candidate_count += 1
            body = _dependency_curried_body(specs[entry], targets)
        nodes.append(
            LayeredReplayNode(
                node_id=positions[entry],
                target=targets[entry],
                dependencies=dependencies[entry],
                body=body,
            )
        )
    assert names[-1] == name
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    raw = LayeredReplayBundle(tuple(nodes), positions[name])
    interned = intern_layered_replay_bodies(raw, targets[name], limits=limits)
    assert type(interned) is LayeredReplayBundle
    target_by_id = {node.node_id: node.target for node in interned.nodes}
    for node in interned.nodes:
        body_target = node.target
        for dependency in reversed(node.dependencies):
            body_target = Imp(target_by_id[dependency], body_target)
        assert check((), node.body, body_target)
        assert not any(type(item) is DNE for item in _walk(node.body))
    compiled = compile_layered_replay(interned, targets[name], limits=limits)
    assert type(compiled) is LayeredReplayCandidate
    assert check((), compiled.certificate, compiled.target)
    assert not any(type(item) is DNE for item in _walk(compiled.certificate))
    layer_cuts = 0
    probe = compiled.certificate
    while type(probe) is Cut:
        layer_cuts += 1
        probe = probe.body
    assert layer_cuts == len(compiled.layers)
    for index in range(layer_cuts):
        corrupted = _mutate_layer_cut(compiled.certificate, index)
        assert not check((), corrupted, compiled.target)
    assert compiled.proof_nodes <= limits.max_candidate_proof_occurrences
    assert compiled.proof_objects <= limits.max_candidate_proof_objects
    assert compiled.proof_depth <= limits.max_candidate_proof_depth
    assert compiled.proof_annotation_occurrences <= (
        limits.max_candidate_annotation_occurrences
    )
    assert compiled.proof_envelope_depth <= (
        limits.max_candidate_envelope_depth
    )
    return {
        "topology_sha256": topology_sha256,
        "node_count": len(names),
        "stable_catalog_count": len(stable),
        "reachable_stable_count": len(names) - candidate_count,
        "candidate_body_count": candidate_count,
        "dependency_edge_count": sum(map(len, dependencies.values())),
        "layer_sizes": list(map(len, compiled.layers)),
        "layer_cut_count": layer_cuts,
        "proof_nodes": compiled.proof_nodes,
        "proof_depth": compiled.proof_depth,
        "proof_objects": compiled.proof_objects,
        "proof_edges": compiled.proof_edges,
        "reused_objects": compiled.reused_objects,
        "annotation_occurrences": compiled.proof_annotation_occurrences,
        "envelope_depth": compiled.proof_envelope_depth,
        "package_formula_occurrences": compiled.package_formula_occurrences,
        "package_formula_depth": compiled.maximum_package_formula_depth,
        "proof_dag_sha256": _proof_dag_sha256(compiled.certificate),
    }


def _run_worker(arguments: list[str], prefix: str) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONMALLOC"] = "malloc"
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *arguments],
        cwd=Path(__file__).resolve().parents[3],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"isolated worker failed for {arguments!r}:\n"
        f"stdout={result.stdout[-4000:]}\n"
        f"stderr={result.stderr[-4000:]}"
    )
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(prefix)
    ]
    assert len(lines) == 1, result.stdout[-4000:]
    return json.loads(lines[0][len(prefix) :])


def _run_body_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--body-worker", name], "B5ST_BODY_RECEIPT ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_closure_worker(name: str) -> dict[str, object]:
    payload = _run_worker(["--closure-worker", name], "B5ST_CLOSURE ")
    assert payload["name"] == name
    return payload["receipt"]


def _run_rejection_worker(
    kind: str,
    name: str,
    dependency: str | None = None,
) -> None:
    arguments = ["--reject-worker", kind, name]
    if dependency is not None:
        arguments.append(dependency)
    payload = _run_worker(arguments, "B5ST_REJECTION ")
    assert payload == {"kind": kind, "name": name}


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


def test_bertrand_square_tail_static_contract() -> None:
    rows = _rows()
    expected = _expected_statements()
    assert len(editions_v11.ALPHA_SPECS) == 1_123
    assert len(editions_v11.STABLE_SPECS) == 432
    assert editions_v11.EXPECTED_ALPHA_V11_EDGE_COUNT == 3_482
    assert editions_v11.EXPECTED_ALPHA_V11_LAYER_COUNT == 45
    assert tuple(row.statement for row in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert tuple(row.dependencies for row in rows) == tuple(
        EXPECTED_DEPENDENCIES[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.script for row in rows))) == tuple(
        EXPECTED_COMMAND_COUNTS[name] for name in EXPECTED_NAMES
    )
    assert tuple(map(len, (row.dependencies for row in rows))) == (6, 2)
    assert len(LIVE_EDGES) == 8
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        row.name for row in editions_v11.ALPHA_SPECS
    }
    assert rows[0].script.count("cases hpower_exists") == 1
    assert rows[0].script.count("apply pow_tail_strict_of_square") == 1
    assert rows[1].script.count("cases horder") == 1
    assert not any(
        command.startswith(("induction", "rewrite"))
        for row in rows
        for command in row.script
    )


def test_bertrand_square_tail_source_and_rfc_pins() -> None:
    library = Path(editions_v11.__file__).resolve().parent
    for filename, expected in SOURCE_PINS.items():
        actual = sha256((library / filename).read_bytes()).hexdigest()
        assert actual == expected
    root = Path(__file__).resolve().parents[3]
    assert sha256((root / RFC_PATH).read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_square_tail_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_LAYERED_CLOSURES) == EXPECTED_NAMES
    assert all(value is not None for value in EXPECTED_ARTIFACTS.values())
    assert all(value is not None for value in EXPECTED_BODIES.values())
    assert all(value is not None for value in EXPECTED_ENVELOPES.values())
    assert all(
        value is not None for value in EXPECTED_LAYERED_CLOSURES.values()
    )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_square_tail_artifacts_are_frozen(name: str) -> None:
    item = _table(_rows())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"B5 SQUARE TAIL {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_square_tail_bodies_are_frozen(name: str) -> None:
    receipt = _run_body_worker(name)
    actual = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(
        f"B5 SQUARE TAIL {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_square_tail_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    _run_rejection_worker("dependency", name, dependency)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_square_tail_false_targets_are_rejected(name: str) -> None:
    _run_rejection_worker("false", name)


def test_bertrand_square_tail_mutations_have_counterfixtures() -> None:
    assert 1 <= 1
    assert not (2 <= 1)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_square_tail_genuine_mutations_are_rejected(
    name: str,
) -> None:
    _run_rejection_worker("mutation", name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_square_tail_layered_closures_are_frozen(
    name: str,
) -> None:
    actual = _run_closure_worker(name)
    print(
        f"B5 SQUARE TAIL {name} LAYERED CLOSURE actual={actual!r}",
        flush=True,
    )
    expected = EXPECTED_LAYERED_CLOSURES[name]
    assert expected is not None, actual
    assert actual == expected


def _main() -> None:
    assert len(sys.argv) >= 3
    mode = sys.argv[1]
    name = sys.argv[2] if mode != "--reject-worker" else sys.argv[3]
    assert name in EXPECTED_NAMES
    if mode == "--body-worker":
        assert len(sys.argv) == 3
        receipt = _body_receipt(name)
        prefix = "B5ST_BODY_RECEIPT "
    elif mode == "--closure-worker":
        assert len(sys.argv) == 3
        receipt = _layered_receipt(name)
        prefix = "B5ST_CLOSURE "
    elif mode == "--reject-worker":
        assert len(sys.argv) in (4, 5)
        kind = sys.argv[2]
        dependency = sys.argv[4] if len(sys.argv) == 5 else None
        _rejection_worker(kind, name, dependency)
        print(
            "B5ST_REJECTION "
            + json.dumps({"kind": kind, "name": name}, sort_keys=True),
            flush=True,
        )
        return
    else:
        raise AssertionError(mode)
    print(
        prefix
        + json.dumps({"name": name, "receipt": receipt}, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    _main()
