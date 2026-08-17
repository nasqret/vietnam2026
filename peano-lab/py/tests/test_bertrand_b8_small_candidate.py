"""Fail-closed audit for the constructive B8 small-range theorem."""

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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero, parse_term_in_context, pretty_term
from peano_lab.library import (
    alpha_enrollment_v11,
    bertrand_b8_covering_candidate,
    bertrand_b8_prime_certificates_candidate,
    bertrand_b8_small_candidate as module,
    bertrand_primorial_choose_interval_candidate,
    bertrand_primorial_foundation_candidate,
    bertrand_primorial_membership_candidate,
    editions_v11,
    theorems as stable_module,
)
from peano_lab.library.bertrand_b8_covering_candidate import (
    BERTRAND_ADD_SWAP_NESTED,
    BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
    BERTRAND_COVER_FIVE_SEVEN,
    BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
    BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
    BERTRAND_COVER_ONE_TWO,
    BERTRAND_COVER_SEVEN_THIRTEEN,
    BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
    BERTRAND_COVER_THREE_FIVE,
    BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
    BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
    BERTRAND_COVER_TWO_THREE,
    BERTRAND_COVERING_INTERVAL,
    make_bertrand_b8_covering_candidate_theorems,
)
from peano_lab.library.bertrand_b8_prime_certificates_candidate import (
    PRIME_EIGHTY_THREE,
    PRIME_FIVE,
    PRIME_FIVE_HUNDRED_TWENTY_ONE,
    PRIME_FORTY_THREE,
    PRIME_ONE_HUNDRED_SIXTY_THREE,
    PRIME_SEVEN,
    PRIME_THIRTEEN,
    PRIME_THREE_HUNDRED_SEVENTEEN,
    PRIME_TWENTY_THREE,
    make_bertrand_b8_prime_certificate_candidate_theorems,
)
from peano_lab.library.bertrand_b8_small_candidate import (
    BERTRAND_CUTOFF_LT_FINAL_PRIME,
    BERTRAND_SMALL_CLOSED_UPPER,
    make_bertrand_b8_small_candidate_theorems,
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


EXPECTED_NAMES = (
    BERTRAND_CUTOFF_LT_FINAL_PRIME,
    BERTRAND_SMALL_CLOSED_UPPER,
)
EXECUTION_NAMES = tuple(reversed(EXPECTED_NAMES))

_CUTOFF = "16 * 32"
_FINAL_PRIME = "2 * (11 * 22) + 37"
_CHAIN = (
    ("1", "2", "prime_two", BERTRAND_COVER_ONE_TWO),
    ("2", "3", "prime_three", BERTRAND_COVER_TWO_THREE),
    ("3", "5", PRIME_FIVE, BERTRAND_COVER_THREE_FIVE),
    ("5", "7", PRIME_SEVEN, BERTRAND_COVER_FIVE_SEVEN),
    ("7", "13", PRIME_THIRTEEN, BERTRAND_COVER_SEVEN_THIRTEEN),
    (
        "13",
        "23",
        PRIME_TWENTY_THREE,
        BERTRAND_COVER_THIRTEEN_TWENTY_THREE,
    ),
    (
        "23",
        "43",
        PRIME_FORTY_THREE,
        BERTRAND_COVER_TWENTY_THREE_FORTY_THREE,
    ),
    (
        "43",
        "9 * 9 + 2",
        PRIME_EIGHTY_THREE,
        BERTRAND_COVER_FORTY_THREE_EIGHTY_THREE,
    ),
    (
        "9 * 9 + 2",
        "13 * 12 + 7",
        PRIME_ONE_HUNDRED_SIXTY_THREE,
        BERTRAND_COVER_EIGHTY_THREE_ONE_HUNDRED_SIXTY_THREE,
    ),
    (
        "13 * 12 + 7",
        "18 * 17 + 11",
        PRIME_THREE_HUNDRED_SEVENTEEN,
        BERTRAND_COVER_ONE_HUNDRED_SIXTY_THREE_THREE_HUNDRED_SEVENTEEN,
    ),
    (
        "18 * 17 + 11",
        _FINAL_PRIME,
        PRIME_FIVE_HUNDRED_TWENTY_ONE,
        BERTRAND_COVER_THREE_HUNDRED_SEVENTEEN_FIVE_HUNDRED_TWENTY_ONE,
    ),
)

EXPECTED_DEPENDENCIES = {
    BERTRAND_CUTOFF_LT_FINAL_PRIME: (
        "add_succ_left",
        "mul_add",
        BERTRAND_ADD_SWAP_NESTED,
        "mul_comm",
        "add_mul",
        "add_assoc",
        "add_comm",
        "mul_assoc",
    ),
    BERTRAND_SMALL_CLOSED_UPPER: (
        "nonzero_is_succ",
        "le_or_lt",
        "lt_trans",
        BERTRAND_CUTOFF_LT_FINAL_PRIME,
        BERTRAND_COVERING_INTERVAL,
        *(item for row in reversed(_CHAIN) for item in row[2:]),
    ),
}
EXPECTED_DIRECT_CUTS = {
    name: len(EXPECTED_DEPENDENCIES[name]) for name in EXPECTED_NAMES
}

SOURCE_PINS = {
    "peano-lab/py/peano_lab/library/theorems.py":
        "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v11.py":
        "400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093",
    "peano-lab/py/peano_lab/library/editions_v11.py":
        "10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_primorial_choose_interval_candidate.py"
    ): "5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_primorial_foundation_candidate.py"
    ): "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_primorial_membership_candidate.py"
    ): "edf14adde5edbbc6b7836003a174ee9a4b84f708fdcd0f3c3af45fc5013ac817",
    (
        "peano-lab/py/peano_lab/library/"
        "bertrand_b8_prime_certificates_candidate.py"
    ): "e38954201d57680644ec6353d7d4c25b320f720d36f07c1c32d590c7920d3387",
    (
        "peano-lab/py/peano_lab/library/bertrand_b8_covering_candidate.py"
    ): "cd44578fee0cf4aa362f925d9f13bc8b64f511e4d3f628a40b5432e59b72b31e",
    (
        "peano-lab/py/peano_lab/library/bertrand_b8_small_candidate.py"
    ): "2886dc0bc4ac85667ec5223ed0074794ff66f828e34e7dbd2791757d141702b0",
}

RFC_PINS = {
    (
        "research/arithmetic-library/"
        "ha-bertrand-postulate-campaign-rfc-v1.md"
    ): "0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b",
    (
        "research/arithmetic-library/"
        "ha-bertrand-postulate-campaign-rfc-v2.md"
    ): "af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b8-prime-certificates-tranche-rfc-v1.md"
    ): "356e8d69498f117921b1229c9a07b42f9caad48febe612a2e89ab93578a3ba73",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b8-covering-tranche-rfc-v1.md"
    ): "1c21f5eb30e7f34ac41013aa10da736f7604696829a907134c6b6b9e3e7720f5",
    (
        "research/arithmetic-library/"
        "ha-bertrand-b8-small-range-tranche-rfc-v1.md"
    ): "08ee855a908faa9e990f75b22a8d599314e446c5bc39773196c79d3130b85891",
}

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    BERTRAND_CUTOFF_LT_FINAL_PRIME: (
        94,
        "522624e2a1afb6f17ce7aa3aa2beacf1bb5a3d72f8932a823639b18b6643a1f2",
        "7f06f163b11329061a97ba36d1bb449fae58dc7cb9ffbf49f02ccafa4e7bd6e5",
        "90baa8e75a1db975bc4d6ca56674663106c3b7006f10929dd6a1d97fdefb3777",
    ),
    BERTRAND_SMALL_CLOSED_UPPER: (
        491,
        "a73902264a153122501ac0007f0f2e8a2137735d5a65a6ff56898f612c9e55ec",
        "98f82a6f21d166c23609e0194277ed1d8f4093937a57795ff0d0344221a79ae8",
        "201ad00315df3e6d2fa56625e0466532b4ca1b1b3c470f0f67afba836f3313d1",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    BERTRAND_CUTOFF_LT_FINAL_PRIME: (8, 103, 2465, 216, 2465, 2464, 0),
    BERTRAND_SMALL_CLOSED_UPPER: (27, 179, 227, 49, 227, 226, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    BERTRAND_CUTOFF_LT_FINAL_PRIME: (2465, 2465, 216, 22473, 225),
    BERTRAND_SMALL_CLOSED_UPPER: (227, 227, 49, 903, 90),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    BERTRAND_CUTOFF_LT_FINAL_PRIME: (
        3466,
        216,
        2783,
        2826,
        44,
        26336,
        225,
        "79aed2c3c74cd145835c42f98b3a8b9db2771f7771dcb400942bae9d143f7a22",
    ),
    BERTRAND_SMALL_CLOSED_UPPER: (
        162138,
        220,
        50637,
        50896,
        260,
        561973,
        229,
        "5cf156c6fe50c5d663633cac8eeb1ba3232ebb25950adfea58c48ac8e45dd5c8",
    ),
}

_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _context(variables: tuple[str, ...]) -> tuple[str, ...]:
    assert isinstance(variables, tuple)
    assert len(set(variables)) == len(variables)
    for value in variables:
        assert value and value not in _RESERVED
        assert value[0].isalpha() or value[0] == "_"
        assert all(character.isalnum() or character in "_'" for character in value)
    return variables


def _render(source: str, variables: tuple[str, ...]) -> str:
    context = _context(variables)
    term = parse_term_in_context(source, list(context))
    return pretty_term(term, list(context)).replace("·", "*")


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    assert tag and tag not in _RESERVED and " " not in tag
    names = tuple(f"bpr_{stem}_{tag}" for stem in stems)
    assert not set(names) & set(variables)
    return names


def _prime(value: str, *, tag: str, variables: tuple[str, ...]) -> str:
    context = _context(variables)
    rendered = _render(value, context)
    left, right = _binders(tag, context, ("left", "right"))
    return (
        f"(~({rendered} = 1) /\\ forall {left} {right}. "
        f"{rendered} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def _lt(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_left = _render(left, context)
    rendered_right = _render(right, context)
    (gap,) = _binders(tag, context, ("gap",))
    return f"exists {gap}. {gap} + S ({rendered_left}) = {rendered_right}"


def _le(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    context = _context(variables)
    rendered_left = _render(left, context)
    rendered_right = _render(right, context)
    (gap,) = _binders(tag, context, ("le_gap",))
    return f"exists {gap}. {gap} + ({rendered_left}) = ({rendered_right})"


def _small_statement(
    *,
    premise: str = "~(n = 0)",
    lower_left: str = "n",
    upper_right: str = "n + n",
) -> str:
    variables = ("n",)
    result_variables = variables + ("p",)
    cutoff = _lt(
        "n", _CUTOFF, tag="bb8s_cutoff_bound", variables=variables
    )
    prime = _prime(
        "p", tag="bb8s_result_prime", variables=result_variables
    )
    lower = _lt(
        lower_left,
        "p",
        tag="bb8s_result_lower",
        variables=result_variables,
    )
    upper = _le(
        "p",
        upper_right,
        tag="bb8s_result_upper",
        variables=result_variables,
    )
    result = f"exists p. ({prime}) /\\ (({lower}) /\\ ({upper}))"
    return f"forall n. {premise} -> ({cutoff}) -> ({result})"


def _expected_statements() -> dict[str, str]:
    return {
        BERTRAND_CUTOFF_LT_FINAL_PRIME: _lt(
            _CUTOFF,
            _FINAL_PRIME,
            tag="bb8s_cutoff_final",
            variables=(),
        ),
        BERTRAND_SMALL_CLOSED_UPPER: _small_statement(),
    }


def _expected_cutoff_script() -> tuple[str, ...]:
    common_left = "22 * 16 + (10 * 6 + (9 + 10 * 10))"
    common_right = "22 * 16 + (10 * 6 + (12 * 6 + 37))"
    return (
        "exists 8",
        f"have hsucc : 8 + S ({_CUTOFF}) = 9 + ({_CUTOFF})",
        f"trans S (8 + ({_CUTOFF}))",
        "apply PA4", "symm", "apply add_succ_left",
        "have h32 : 32 = 22 + 10", "norm_num",
        f"have hleft : 9 + ({_CUTOFF}) = {common_left}",
        "rewrite h32", "trans 9 + (16 * 22 + 16 * 10)",
        "congr", "refl", "apply mul_add",
        "trans 16 * 22 + (9 + 16 * 10)",
        f"apply {BERTRAND_ADD_SWAP_NESTED}",
        "trans 22 * 16 + (9 + 16 * 10)",
        "congr", "apply mul_comm", "refl",
        "have h16 : 16 = 10 + 6", "norm_num",
        "have htail16 : 16 * 10 = (10 + 6) * 10",
        "congr", "exact h16", "refl", "rewrite htail16",
        "trans 22 * 16 + (9 + (10 * 10 + 6 * 10))",
        "congr", "refl", "congr", "refl", "apply add_mul",
        "trans 22 * 16 + (9 + (10 * 10 + 10 * 6))",
        "congr", "refl", "congr", "refl", "congr", "refl",
        "apply mul_comm",
        "trans 22 * 16 + ((9 + 10 * 10) + 10 * 6)",
        "congr", "refl", "symm", "apply add_assoc",
        f"trans {common_left}",
        "congr", "refl", "apply add_comm", "refl",
        "have htwoeleven : 2 * 11 = 22", "norm_num",
        "have h22sixteen : 22 = 16 + 6", "norm_num",
        "have h22twelve : 22 = 10 + 12", "norm_num",
        f"have hright : ({_FINAL_PRIME}) = {common_right}",
        "trans (2 * 11) * 22 + 37", "congr", "symm",
        "apply mul_assoc", "refl", "rewrite htwoeleven",
        "trans 22 * (16 + 6) + 37", "congr", "congr", "refl",
        "exact h22sixteen", "refl",
        "trans (22 * 16 + 22 * 6) + 37", "congr",
        "apply mul_add", "refl",
        "trans 22 * 16 + (22 * 6 + 37)", "apply add_assoc",
        "have htail22 : 22 * 6 = (10 + 12) * 6",
        "congr", "exact h22twelve", "refl", "rewrite htail22",
        "trans 22 * 16 + ((10 * 6 + 12 * 6) + 37)",
        "congr", "refl", "congr", "apply add_mul", "refl",
        f"trans {common_right}",
        "congr", "refl", "apply add_assoc", "refl",
        "have htail : 9 + 10 * 10 = 12 * 6 + 37", "norm_num",
        "rewrite htail at hleft",
        f"have hcarrier : 9 + ({_CUTOFF}) = ({_FINAL_PRIME})",
        f"trans {common_right}", "exact hleft", "symm", "exact hright",
        f"trans 9 + ({_CUTOFF})", "exact hsucc", "exact hcarrier",
    )


def _cover_application(
    left: str,
    right: str,
    prime_name: str,
    cover_name: str,
    lower_name: str,
    strict_name: str,
) -> tuple[str, ...]:
    return (
        f"specialize {BERTRAND_COVERING_INTERVAL} ({left})",
        f"specialize {BERTRAND_COVERING_INTERVAL} ({right})",
        f"specialize {BERTRAND_COVERING_INTERVAL} n",
        f"apply {BERTRAND_COVERING_INTERVAL}",
        f"exact {prime_name}", f"exact {lower_name}",
        f"exact {strict_name}", f"exact {cover_name}",
    )


def _expected_small_script() -> tuple[str, ...]:
    script = [
        "intro n", "intro hnonzero", "intro hcutoff",
        "have hshape : exists k. n = S k",
        "specialize nonzero_is_succ n", "apply nonzero_is_succ",
        "exact hnonzero", "cases hshape",
        "have hlower_1 : exists k. k + 1 = n", "exists x",
        "rewrite hshape_witness", "rewrite PA4", "rewrite PA3", "refl",
    ]
    lower_name = "hlower_1"
    for index, (_left, right, _prime_name, _cover_name) in enumerate(
        _CHAIN[:-1], start=1
    ):
        split_name = f"hsplit_{index}"
        next_lower = f"hlower_{index + 1}"
        script.extend(
            (
                f"have {split_name} : (exists k. k + ({right}) = n) \\/ "
                f"(exists k. k + S n = ({right}))",
                f"specialize le_or_lt ({right})",
                "specialize le_or_lt n", "exact le_or_lt",
                f"cases {split_name}",
                f"have {next_lower} : exists k. k + ({right}) = n",
                f"exact {split_name}_left",
            )
        )
        lower_name = next_lower
    final_left, final_right, final_prime, final_cover = _CHAIN[-1]
    script.extend(
        (
            f"have hfinal_strict : exists k. k + S n = ({final_right})",
            "specialize lt_trans n", f"specialize lt_trans ({_CUTOFF})",
            f"specialize lt_trans ({final_right})", "apply lt_trans",
            "exact hcutoff", f"exact {BERTRAND_CUTOFF_LT_FINAL_PRIME}",
            *_cover_application(
                final_left, final_right, final_prime, final_cover,
                lower_name, "hfinal_strict",
            ),
        )
    )
    for index in range(len(_CHAIN) - 1, 0, -1):
        left, right, prime_name, cover_name = _CHAIN[index - 1]
        branch_lower = "hlower_1" if index == 1 else f"hlower_{index}"
        script.extend(
            _cover_application(
                left, right, prime_name, cover_name, branch_lower,
                f"hsplit_{index}_right",
            )
        )
    return tuple(script)


EXPECTED_SCRIPTS = {
    BERTRAND_CUTOFF_LT_FINAL_PRIME: _expected_cutoff_script(),
    BERTRAND_SMALL_CLOSED_UPPER: _expected_small_script(),
}


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    primes = make_bertrand_b8_prime_certificate_candidate_theorems(
        TheoremSpec
    )
    covers = make_bertrand_b8_covering_candidate_theorems(TheoremSpec)
    rows = primes + covers
    assert len(rows) == 32
    assert len({row.name for row in rows}) == len(rows)
    return rows


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    rows = make_bertrand_b8_small_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return rows


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {row.name: row for row in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return _specs_by_name() | _table(_support_specs())


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _core() | _table(_specs()[:index])


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
        assert tactic != "use"
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _close(
    name: str,
    cache: dict[str, tuple[Formula, Proof]] | None = None,
) -> tuple[Formula, Proof]:
    if cache is None:
        cache = {}
    if name in cache:
        return cache[name]
    public = _specs_by_name()
    if name in public:
        checked = replay(name)
        result = (checked.formula, checked.certificate)
        cache[name] = result
        return result
    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    dependencies = tuple(
        _close(dependency, cache) for dependency in item.dependencies
    )
    for dependency_formula, dependency_proof in reversed(dependencies):
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    result = (formula, body)
    cache[name] = result
    return result


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


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _body_receipt(name: str) -> dict[str, object]:
    item = _table(_specs())[name]
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
        label=f"B8 small body {name}",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual = (
        len(item.dependencies), len(item.script), nodes, depth,
        objects, edges, reused,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    return {"body": list(actual), "envelope": list(envelope)}


def _closure_receipt(name: str) -> list[object]:
    item = _table(_specs())[name]
    formula, certificate = _close(name)
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
        label=f"B8 small closure {name}",
    )
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual: list[object] = [
        nodes, depth, objects, edges, reused, envelope[3], envelope[4],
        _proof_dag_sha256(certificate),
    ]
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(certificate))
    direct_cut_count = 0
    probe = certificate
    while type(probe) is Cut:
        direct_cut_count += 1
        probe = probe.body
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cut_count):
        assert not check((), _mutate_direct_cut(certificate, index), formula)
    return actual


def _mutation_statements() -> dict[tuple[str, str], str]:
    return {
        (BERTRAND_CUTOFF_LT_FINAL_PRIME, "larger_cutoff"): _lt(
            "17 * 32", _FINAL_PRIME,
            tag="bb8s_cutoff_final", variables=(),
        ),
        (BERTRAND_CUTOFF_LT_FINAL_PRIME, "smaller_final"): _lt(
            _CUTOFF, "2 * (11 * 22) + 28",
            tag="bb8s_cutoff_final", variables=(),
        ),
        (BERTRAND_SMALL_CLOSED_UPPER, "zero_input"): _small_statement(
            premise="n = 0"
        ),
        (BERTRAND_SMALL_CLOSED_UPPER, "upper_at_n"): _small_statement(
            upper_right="n"
        ),
        (BERTRAND_SMALL_CLOSED_UPPER, "shifted_lower"): _small_statement(
            lower_left="S n"
        ),
    }


def _rejection_worker(kind: str, name: str, key: str | None) -> None:
    item = _table(_specs())[name]
    if kind == "dependency":
        assert key in item.dependencies
        changed = replace(
            item,
            dependencies=tuple(x for x in item.dependencies if x != key),
        )
    elif kind == "false":
        assert key is None
        changed = replace(item, statement=f"({item.statement}) /\\ false")
    elif kind == "mutation":
        assert key is not None
        changed = replace(item, statement=_mutation_statements()[(name, key)])
    else:
        raise AssertionError(kind)
    try:
        replay_candidate_bodies((changed,), core=_row_core(name))
    except CandidateBodyError:
        return
    raise AssertionError(f"{kind} mutation unexpectedly replayed for {name}")


def _run_worker(arguments: list[str], prefix: str) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONMALLOC"] = "malloc"
    python_root = str(Path(__file__).resolve().parents[1])
    inherited_path = environment.get("PYTHONPATH")
    pieces = [python_root]
    if inherited_path:
        pieces.append(inherited_path)
    environment["PYTHONPATH"] = os.pathsep.join(pieces)
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *arguments],
        cwd=_repository_root(),
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
    lines = [line for line in result.stdout.splitlines() if line.startswith(prefix)]
    assert len(lines) == 1, result.stdout[-4000:]
    return json.loads(lines[0][len(prefix) :])


def _run_rejection(kind: str, name: str, key: str | None = None) -> None:
    arguments = ["--reject-worker", kind, name]
    if key is not None:
        arguments.append(key)
    payload = _run_worker(arguments, "B8S_REJECTION ")
    assert payload == {"kind": kind, "name": name}


def test_b8_small_sources_and_contracts_are_pinned() -> None:
    providers = {
        stable_module: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/theorems.py"
        ],
        alpha_enrollment_v11: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/alpha_enrollment_v11.py"
        ],
        editions_v11: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/editions_v11.py"
        ],
        bertrand_primorial_choose_interval_candidate: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/"
            "bertrand_primorial_choose_interval_candidate.py"
        ],
        bertrand_primorial_foundation_candidate: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/"
            "bertrand_primorial_foundation_candidate.py"
        ],
        bertrand_primorial_membership_candidate: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/"
            "bertrand_primorial_membership_candidate.py"
        ],
        bertrand_b8_prime_certificates_candidate: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/"
            "bertrand_b8_prime_certificates_candidate.py"
        ],
        bertrand_b8_covering_candidate: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/bertrand_b8_covering_candidate.py"
        ],
        module: SOURCE_PINS[
            "peano-lab/py/peano_lab/library/bertrand_b8_small_candidate.py"
        ],
    }
    for provider, digest in providers.items():
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest
    root = _repository_root()
    for relative, digest in RFC_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest


def test_b8_small_factory_is_exact_and_isolated() -> None:
    expected = _expected_statements()
    stable = _specs_by_name()
    alpha_names = {row.name for row in editions_v11.ALPHA_SPECS}
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS.values()) == (8, 27)
    assert sum(EXPECTED_DIRECT_CUTS.values()) == 35
    assert tuple(row.name for row in _specs()) == EXPECTED_NAMES
    assert not set(EXPECTED_NAMES) & set(stable)
    assert not set(EXPECTED_NAMES) & alpha_names
    for row in _specs():
        assert row.statement == expected[row.name]
        assert row.dependencies == EXPECTED_DEPENDENCIES[row.name]
        parsed, free_names = parse_formula_with_names(row.statement)
        assert isinstance(parsed, Formula)
        assert not free_names
        assert parsed == _closed_formula(row.statement)
    assert tuple(module.__all__) == (
        "BERTRAND_CUTOFF_LT_FINAL_PRIME",
        "BERTRAND_SMALL_CLOSED_UPPER",
        "make_bertrand_b8_small_candidate_theorems",
    )
    token = "bertrand_b8_small_candidate"
    for authority in (stable_module, alpha_enrollment_v11, editions_v11):
        assert token not in Path(authority.__file__).read_text(encoding="utf-8")


def test_b8_small_scripts_are_exact_and_constructive() -> None:
    rows = _table(_specs())
    assert rows[BERTRAND_CUTOFF_LT_FINAL_PRIME].script == (
        EXPECTED_SCRIPTS[BERTRAND_CUTOFF_LT_FINAL_PRIME]
    )
    assert rows[BERTRAND_SMALL_CLOSED_UPPER].script == (
        EXPECTED_SCRIPTS[BERTRAND_SMALL_CLOSED_UPPER]
    )
    assert len(rows[BERTRAND_CUTOFF_LT_FINAL_PRIME].script) == 103
    assert len(rows[BERTRAND_SMALL_CLOSED_UPPER].script) == 179
    assert rows[BERTRAND_CUTOFF_LT_FINAL_PRIME].script.count("norm_num") == 6
    assert rows[BERTRAND_SMALL_CLOSED_UPPER].script.count(
        "specialize le_or_lt n"
    ) == 10
    assert rows[BERTRAND_SMALL_CLOSED_UPPER].script.count(
        f"apply {BERTRAND_COVERING_INTERVAL}"
    ) == 11
    forbidden = ("DNE", "by_contra", "classical", "sorry", "use ", "induction ")
    for row in rows.values():
        assert not any(
            token in command
            for command in row.script
            for token in forbidden
        )
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert '"512"' not in source and '"521"' not in source


def test_b8_small_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_b8_small_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256("\0".join((item.statement, *item.dependencies)).encode()).hexdigest(),
    )
    print(f"B8 SMALL {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, actual
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_b8_small_bodies_and_envelopes_are_frozen(name: str) -> None:
    payload = _run_worker(["--body-worker", name], "B8S_BODY ")
    receipt = payload["receipt"]
    actual = tuple(receipt["body"])
    envelope = tuple(receipt["envelope"])
    print(
        f"B8 SMALL {name} BODY actual={actual!r} envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXECUTION_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == len(set(LIVE_EDGES)) == 35


@pytest.mark.parametrize(
    ("name", "dependency"),
    LIVE_EDGES,
    ids=tuple(f"{name}--{dependency}" for name, dependency in LIVE_EDGES),
)
def test_b8_small_every_dependency_is_live(name: str, dependency: str) -> None:
    _run_rejection("dependency", name, dependency)


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_b8_small_false_targets_are_rejected(name: str) -> None:
    _run_rejection("false", name)


def test_b8_small_mutations_have_counterfixtures() -> None:
    assert not 17 * 32 < 2 * (11 * 22) + 37
    assert not 16 * 32 < 2 * (11 * 22) + 28
    assert not any(0 < p <= 0 for p in range(1))
    assert not any(1 < p <= 1 for p in range(2))
    assert not any(2 < p <= 2 for p in range(3))


@pytest.mark.parametrize(
    ("name", "case_id"),
    tuple(_mutation_statements()),
    ids=tuple(case_id for _name, case_id in _mutation_statements()),
)
def test_b8_small_genuine_mutations_are_rejected(
    name: str,
    case_id: str,
) -> None:
    _run_rejection("mutation", name, case_id)


@pytest.mark.parametrize("name", EXECUTION_NAMES)
def test_b8_small_independent_closures_are_frozen(name: str) -> None:
    payload = _run_worker(["--closure-worker", name], "B8S_CLOSURE ")
    actual = tuple(payload["receipt"])
    print(f"B8 SMALL {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_CLOSURES[name]


def _main() -> None:
    assert len(sys.argv) >= 3
    mode = sys.argv[1]
    if mode == "--reject-worker":
        assert len(sys.argv) in (4, 5)
        kind, name = sys.argv[2:4]
        key = sys.argv[4] if len(sys.argv) == 5 else None
        _rejection_worker(kind, name, key)
        print(
            "B8S_REJECTION "
            + json.dumps({"kind": kind, "name": name}, sort_keys=True),
            flush=True,
        )
        return
    assert len(sys.argv) == 3
    name = sys.argv[2]
    assert name in EXPECTED_NAMES
    if mode == "--body-worker":
        receipt: object = _body_receipt(name)
        prefix = "B8S_BODY "
    elif mode == "--closure-worker":
        receipt = _closure_receipt(name)
        prefix = "B8S_CLOSURE "
    else:
        raise AssertionError(mode)
    print(
        prefix
        + json.dumps({"name": name, "receipt": receipt}, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    _main()
