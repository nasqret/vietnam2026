"""Focused strict-HA audit for the canonical signed decoder candidates."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_signed_decode_candidate import (
    make_ha_signed_decode_candidate_theorems,
    signed_decode,
    signed_valid,
)
from peano_lab.library.ha_signed_parity_candidate import (
    make_ha_signed_parity_candidate_theorems,
)
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "signed_decode_nonnegative_constructor",
    "signed_decode_negative_constructor",
    "signed_decode_total",
    "signed_decode_normal",
    "signed_decode_functional",
    "signed_decode_zero_iff",
    "signed_valid_all",
)
EXPECTED_DEPENDENCIES = {
    "signed_decode_nonnegative_constructor": (),
    "signed_decode_negative_constructor": (),
    "signed_decode_total": ("parity_cases",),
    "signed_decode_normal": (),
    "signed_decode_functional": (
        "even_half_unique",
        "odd_half_unique",
        "even_odd_exclusive_k1",
    ),
    "signed_decode_zero_iff": ("succ_ne_zero",),
    "signed_valid_all": ("signed_decode_total",),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_decode_nonnegative_constructor":
        "57e7cea7350808ca4a08b8b071d12f14aae1f940802d656bf8bfba6dcdd0c147",
    "signed_decode_negative_constructor":
        "4b08b44ec3135c9f4e15179b0ad4747559ca5c58e333e2f287682f4be968e225",
    "signed_decode_total":
        "c057ebd0f11884b8c25ade6f499a867c82213a4257ae911d3362737171491bb9",
    "signed_decode_normal":
        "b4d32211ca796e93d4bb4f94534ceaa1932f0ab67774b21adee330c421d24064",
    "signed_decode_functional":
        "e381856c7267dbe693135733ee309e3959dcafd9b4be4bd8bd6882ffa15fbedb",
    "signed_decode_zero_iff":
        "8da5c49e4ae509ea35fc66dad04eff81833213b64e72e790549133deb2a2a6b1",
    "signed_valid_all":
        "2ae61c98b77f52bf86c2db02a7368bc0441456ed990881a1bac493e2652498ab",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_decode_nonnegative_constructor": (0, 5, 5, 4, 5, 4, 0),
    "signed_decode_negative_constructor": (0, 8, 8, 6, 8, 7, 0),
    "signed_decode_total": (1, 19, 25, 13, 25, 24, 0),
    "signed_decode_normal": (0, 13, 36, 16, 36, 35, 0),
    "signed_decode_functional": (3, 66, 92, 24, 92, 91, 0),
    "signed_decode_zero_iff": (1, 21, 52, 16, 52, 51, 0),
    "signed_valid_all": (1, 3, 7, 5, 7, 6, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_decode_nonnegative_constructor": (
        5,
        4,
        5,
        4,
        0,
        0,
        "f2815aa28738f977ee0fa4c7e513009501f86aa65c75b7838aec2281bef156ef",
    ),
    "signed_decode_negative_constructor": (
        8,
        6,
        8,
        7,
        0,
        0,
        "53a7aa3e7f60cfb748907a52dded47db788ff90fd678d085ac1ac7cf5dfd5f9d",
    ),
    "signed_decode_total": (
        105,
        20,
        98,
        104,
        7,
        1,
        "6fb3f4a4676053040dd545cc96aeace9298f840ce3c7e6f147061a4b49416ac1",
    ),
    "signed_decode_normal": (
        36,
        16,
        36,
        35,
        0,
        0,
        "b2ba8b659c6dc22928b0a0475936646ef67e226556ca64e9cc8237e3d8b11322",
    ),
    "signed_decode_functional": (
        709,
        27,
        397,
        399,
        3,
        13,
        "50818b66647097dee0680f1dacbcb62368049dcc95f66532cd36b63306ab3c0b",
    ),
    "signed_decode_zero_iff": (
        53,
        16,
        53,
        52,
        0,
        1,
        "7a1f625296bbcbaf16692e309b7119d2704f20bde270b96fbe6a0e8b79226fc9",
    ),
    "signed_valid_all": (
        112,
        21,
        105,
        111,
        7,
        2,
        "38b54ca5dfbe1381f5baf011ed3082819e6164cce28f0314b324b618890f0e78",
    ),
}
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_eq_zero_right",
    "add_right_cancel",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "odd_half_unique",
    "parity_cases",
    "succ_ne_zero",
    "zero_or_succ",
}
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "even_half_unique",
    "even_odd_exclusive_k1",
    "signed_decode_total",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)
RFC_SIGNED_DECODE = (
    "(code = 2 * pos /\\ neg = 0) \\/ exists half. "
    "((code = 2 * half + 1 /\\ pos = 0) /\\ neg = S half)"
)
RFC_SIGNED_VALID = (
    "exists pos neg. ((code = 2 * pos /\\ neg = 0) \\/ exists half. "
    "((code = 2 * half + 1 /\\ pos = 0) /\\ neg = S half))"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SIGNED_RFC_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "arithmetic-library"
    / "ha-canonical-signed-natural-rfc-v1.md"
)


@lru_cache(maxsize=1)
def _parity_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_parity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_decode_candidate_theorems(TheoremSpec)


def _local_specs() -> dict[str, TheoremSpec]:
    return {
        item.name: item for item in (*_parity_specs(), *_candidate_specs())
    }


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


def _cold_closed_receipts() -> dict[str, tuple[int, int, int, int, int, int, str]]:
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
            assert type(body) is ImpIntro, (
                f"{item.name} did not expose dependency {dependency}"
            )
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


def _decode_semantics(code: int, pos: int, neg: int, bound: int) -> bool:
    return (code == 2 * pos and neg == 0) or any(
        code == 2 * half + 1 and pos == 0 and neg == half + 1
        for half in range(bound + 1)
    )


def _rfc_template(identifier: str) -> str:
    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    marker = f"Stable RFC identifier: `{identifier}`."
    assert source.count(marker) == 1
    suffix = source.split(marker, 1)[1]
    assert suffix.startswith("\n\n```text\n")
    return suffix.removeprefix("\n\n```text\n").split("\n```", 1)[0]


def test_signed_decode_factory_is_exact_ordered_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_decode_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_decode_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_decode_surfaces_are_hygienic_and_match_the_rfc() -> None:
    assert _rfc_template("HA-K3-SIGNED-D01") == RFC_SIGNED_DECODE
    assert _rfc_template("HA-K3-SIGNED-D02") == RFC_SIGNED_VALID
    assert sha256(RFC_SIGNED_DECODE.encode()).hexdigest() == (
        "06d5b4bd0034d03439b5976b70074a836ca1598b4c32794d50f1f95691ed7922"
    )
    assert sha256(RFC_SIGNED_VALID.encode()).hexdigest() == (
        "19c754659652d9158c1ac26e86cabc3ddeab385412d4e485861ffffdc9de977a"
    )

    left = signed_decode("code", "pos", "neg", tag="alpha_left")
    right = signed_decode("code", "pos", "neg", tag="alpha_right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    assert parse_formula(left) == parse_formula(RFC_SIGNED_DECODE)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"code", "pos", "neg"}

    valid_left = signed_valid("code", tag="alpha_left")
    valid_right = signed_valid("code", tag="alpha_right")
    assert valid_left != valid_right
    assert parse_formula(valid_left) == parse_formula(valid_right)
    assert parse_formula(valid_left) == parse_formula(RFC_SIGNED_VALID)
    _, valid_free_names = parse_formula_with_names(valid_left)
    assert set(valid_free_names) == {"code"}

    with pytest.raises(ValueError, match="Peano identifier"):
        signed_decode("code + 1", "pos", "neg", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        signed_valid("code", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        signed_decode("sd_half_capture", "pos", "neg", tag="capture")
    with pytest.raises(ValueError, match="captures its argument"):
        signed_valid("sd_pos_capture", tag="capture")


def test_signed_decode_contracts_are_exact_closed_base_ha_formulas() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedValid(",
                "DivRem(",
                "BetaAt(",
                "ModEq(",
                "%",
                "<",
                "<=",
            )
        )

    assert _candidate_specs()[0].statement == (
        "forall p. ((2 * p = 2 * p /\\ 0 = 0) \\/ exists "
        "sd_half_nonnegative. ((2 * p = 2 * sd_half_nonnegative + 1 "
        "/\\ p = 0) /\\ 0 = S sd_half_nonnegative))"
    )
    assert _candidate_specs()[1].statement == (
        "forall k. ((2 * k + 1 = 2 * 0 /\\ S k = 0) \\/ exists "
        "sd_half_negative. ((2 * k + 1 = 2 * sd_half_negative + 1 "
        "/\\ 0 = 0) /\\ S k = S sd_half_negative))"
    )
    assert _candidate_specs()[4].statement.endswith("pos1 = pos2 /\\ neg1 = neg2")
    assert _candidate_specs()[5].statement.startswith("forall code. ((((")
    assert _candidate_specs()[6].statement == _candidate_specs()[2].statement.replace(
        "sd_half_total", "sd_half_valid"
    )


def test_signed_decode_dependencies_are_transitively_k1_only() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    assert "even_odd_exclusive_pointwise" not in public_closure
    assert "division_remainder_unique" not in public_closure

    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_decode_bodies_are_constructive_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | {
        item.name: item for item in _parity_specs()
    }
    receipts = replay_candidate_bodies(specs, core=core)
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
        "signed_decode_nonnegative_constructor": lambda statement: statement.replace(
            "2 * p = 2 * p", "S (2 * p) = 2 * p", 1
        ),
        "signed_decode_negative_constructor": lambda statement: statement.replace(
            "S k = S sd_half_negative", "k = S sd_half_negative", 1
        ),
        "signed_decode_total": lambda statement: statement.replace(
            "2 * sd_half_total + 1",
            "2 * sd_half_total + 2",
            1,
        ),
        "signed_decode_normal": lambda statement: statement.removesuffix(
            "pos = 0 \\/ neg = 0"
        ) + "S pos = 0 \\/ neg = 0",
        "signed_decode_functional": lambda statement: statement.removesuffix(
            "pos1 = pos2 /\\ neg1 = neg2"
        ) + "S pos1 = pos2 /\\ neg1 = neg2",
        "signed_decode_zero_iff": lambda statement: statement.replace(
            ")) -> code = 0) /\\", ")) -> S code = 0) /\\", 1
        ),
        "signed_valid_all": lambda statement: statement.replace(
            "2 * sd_half_valid + 1",
            "2 * sd_half_valid + 2",
            1,
        ),
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_signed_decode_representation_mutations_break_boundary_semantics() -> None:
    def shifted_odd_branch(code: int, pos: int, neg: int, bound: int) -> bool:
        return (code == 2 * pos and neg == 0) or any(
            code == 2 * half + 2 and pos == 0 and neg == half + 1
            for half in range(bound + 1)
        )

    def negative_zero_allowed(code: int, pos: int, neg: int, bound: int) -> bool:
        return (code == 2 * pos and neg == 0) or any(
            code == 2 * half + 1 and pos == 0 and neg == half
            for half in range(bound + 1)
        )

    assert not any(
        shifted_odd_branch(1, pos, neg, 4)
        for pos in range(5)
        for neg in range(5)
    )
    assert negative_zero_allowed(1, 0, 0, 4)
    assert not _decode_semantics(1, 0, 0, 4)

    canonical_fixtures = ((0, 0), (0, 1), (1, 0), (0, 2), (2, 0))
    shifted_fixtures = tuple(
        next(
            (
                (pos, neg)
                for pos in range(6)
                for neg in range(6)
                if shifted_odd_branch(code, pos, neg, 5)
            ),
            None,
        )
        for code in range(5)
    )
    assert shifted_fixtures != canonical_fixtures


def test_signed_decode_bounded_semantics_through_twenty() -> None:
    fixtures = {
        0: (0, 0),
        1: (0, 1),
        2: (1, 0),
        3: (0, 2),
        4: (2, 0),
    }
    for code in range(21):
        expected = (code // 2, 0) if code % 2 == 0 else (0, code // 2 + 1)
        solutions = [
            (pos, neg)
            for pos in range(22)
            for neg in range(22)
            if _decode_semantics(code, pos, neg, 21)
        ]
        assert solutions == [expected]
        assert expected[0] == 0 or expected[1] == 0
        assert (expected == (0, 0)) == (code == 0)
        if code in fixtures:
            assert expected == fixtures[code]

    assert not _decode_semantics(1, 0, 0, 21)
    assert not _decode_semantics(2, 0, 1, 21)
    assert not _decode_semantics(3, 0, 1, 21)


def test_signed_decode_empty_context_closure_is_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()

    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
