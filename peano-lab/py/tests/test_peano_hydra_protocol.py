"""Strict typed HA-development input, provenance, and native transactions."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.batch import capability_sha256, run_proof  # noqa: E402
from peano_lab.engine.state import start  # noqa: E402
from peano_lab.engine.tactics import TacticError, checked_final  # noqa: E402
from peano_lab.engine.trace import TraceLogger, render_goals  # noqa: E402
from peano_lab.kernel.checker import check  # noqa: E402
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.ui.prove import ProofSession, SurfaceCapabilities, run_surface  # noqa: E402
from training.peano_hydra import protocol  # noqa: E402
from training.peano_hydra.protocol import (  # noqa: E402
    ProtocolError, action_receipt, compile_action, development_profile,
    execute_action, validate_statement,
)
from training.peano_policy.search import state_sha256  # noqa: E402


COMMANDS = frozenset({
    "apply", "assumption", "cases", "compact_arith", "exists", "have",
    "induction", "intro", "left", "norm_num", "refl", "rewrite", "right",
    "simp", "specialize", "split", "suffices", "use",
})


def _caps(*, imports: tuple[str, ...] = (), commands: frozenset[str] = COMMANDS) -> SurfaceCapabilities:
    return SurfaceCapabilities(
        label="hydra-protocol-test", allowed_commands=commands,
        allowed_theorems=frozenset(imports),
    )


def _action(op: str, **fields: object) -> dict[str, object]:
    return {"v": 1, "op": op, **fields}


def _dispatch(solver: str, premises: list[str] | None = None) -> dict[str, object]:
    return _action("Dispatch", solver=solver, premises=premises or [], bounds={"max_calls": 1})


def _split(kind: str, name: str | None = None) -> dict[str, object]:
    return _action("Split", kind=kind, name=name)


def _use(name: str, *terms: str) -> dict[str, object]:
    return _action("Use", name=name, specializations=list(terms))


def _owner(source: str) -> ProofSession:
    canonical = validate_statement(source)
    target = parse_formula_in_context(canonical, [])
    return ProofSession(
        state=start(target), original_target=target, original_names=(),
        target_source=source, classical=False, trace=TraceLogger(session_id="protocol-test"),
    )


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def test_profile_is_detached_canonical_source_bound_and_not_a_decision_claim() -> None:
    first = development_profile()
    expected = dict(first)
    digest = expected.pop("profile_sha256")
    assert digest == _digest(expected)
    assert first["profile_id"] == "hydra-ha-development-v1"
    assert first["h0_complete"] is False
    assert first["research_claim_eligible"] is False
    assert first["classical"] is False
    assert first["evidence"]["negative_result_supported"] is False
    assert first["evidence"]["decision_procedure_claim"] is False
    assert first["actions"]["Dispatch"]["external_solvers"] is False
    assert {entry["name"] for entry in first["axioms"]} == {f"PA{i}" for i in range(1, 7)}
    assert "DNE" not in first["proof_rules"]
    for source in first["source_bindings"]:
        raw = (ROOT / source["path"]).read_bytes()
        assert source == {"path": source["path"], "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    first["grammar"]["terms"]["Zero"].append("bad")
    first["source_bindings"].clear()
    assert development_profile()["profile_sha256"] == digest
    assert development_profile()["grammar"]["terms"]["Zero"] == []


@pytest.mark.parametrize(("source", "equivalent"), [
    ("forall n. n + 0 = n", "∀ x. x + 0 = x"),
    ("forall n. exists m. m = n", "forall a. exists b. b = a"),
    ("forall n. ~ (S n = 0)", "forall a. S a = 0 -> bot"),
    ("forall n m. n <= m", "forall a b. exists k. k + a = b"),
    ("forall n. forall n. n = n", "forall a. forall b. b = b"),
    ("(0 = 0 /\\ 1 = 1) -> (0 = 1 \\/ 0 = 0)", "(0 = 0 ∧ 1 = 1) → (0 = 1 ∨ 0 = 0)"),
    ("64 = 64", "S 63 = 64"),
    ("0 = 1", "0 = 1"),
])
def test_statements_are_closed_alpha_canonical_and_sugar_preserving(source: str, equivalent: str) -> None:
    canonical = validate_statement(source)
    assert canonical == validate_statement(equivalent)
    assert canonical == validate_statement(canonical)


def test_non_equivalent_binder_scopes_do_not_collapse() -> None:
    assert validate_statement("forall a. exists b. b = a") != validate_statement("forall a. exists b. b = b")


@pytest.mark.parametrize("source", [
    "n = n", "forall n. n = m", "#0 = #0", "?m = 0", "f(0) = 0", "P(0)",
    "forall n. n < 0", "65 = 65", "999999999999999999999 = 0", "-1 = 0",
    "forall α. α = α", "forall n\u200b. n = n", "０ = 0", "0 = 0\nrefl",
    "999999999999999999999bad = 0", "９９bad = 0",
    "0 = 0; refl", "0 = 0 -- comment", "0 = 0 <|> refl", "0 = 0\u202e", "0 =\t0",
    "forall DNE. DNE = DNE", "forall PA1. PA1 = PA1", "", " ",
    "forall S. 0 = 0", "forall goal. 0 = 0",
    "(" * 49 + "0 = 0" + ")" * 49,
    "forall " + " ".join(f"n{i}" for i in range(17)) + ". 0 = 0",
    "forall " + "n" * 65 + ". 0 = 0",
    "S " * 65 + "0 = 0",
    "0 = 0 " * 700,
    "0" + " + 0" * 130 + " = 0",
])
def test_out_of_profile_statement_is_rejected(source: str) -> None:
    with pytest.raises(ProtocolError):
        validate_statement(source)


@pytest.mark.parametrize("source", [None, 0, True, b"0 = 0", "\ud800 = 0"])
def test_statement_types_and_utf8_are_exact(source: object) -> None:
    with pytest.raises(ProtocolError):
        validate_statement(source)


@pytest.mark.parametrize(("action", "expected"), [
    (_use("h"), ("apply h",)),
    (_use("h", "n", "0 + n"), ("specialize h n", "specialize h 0 + n", "apply h")),
    (_use("PA1"), ("apply PA1",)),
    (_use("PA2"), ("apply PA2",)),
    (_use("PA3"), ("apply PA3",)),
    (_use("PA4"), ("apply PA4",)),
    (_use("PA5"), ("apply PA5",)),
    (_use("PA6"), ("apply PA6",)),
    (_action("Cut", kind="have", name="k", formula="forall m. m = n"), ("have k : ∀ x. x = n",)),
    (_action("Cut", kind="suffices", name="k", formula="n = n"), ("suffices k : n = n",)),
    (_action("Witness", term="S (n + 0)"), ("exists S (n + 0)",)),
    (_action("Induct", variable="n", motive="goal"), ("induction n",)),
    (_action("Rewrite", source="h", direction="forward", location="goal"), ("rewrite h",)),
    (_action("Rewrite", source="h", direction="backward", location="j"), ("rewrite <- h at j",)),
    (_split("intro"), ("intro",)), (_split("intro", "x"), ("intro x",)),
    (_split("and"), ("split",)), (_split("left"), ("left",)), (_split("right"), ("right",)),
    (_split("cases", "h"), ("cases h",)),
    (_dispatch("refl"), ("refl",)), (_dispatch("assumption"), ("assumption",)),
    (_dispatch("norm_num"), ("norm_num",)), (_dispatch("simp", ["h"]), ("simp [h]",)),
    (_dispatch("compact_arith", ["h", "j"]), ("compact_arith [h, j]",)),
])
def test_every_typed_action_compiles_deterministically(action: dict[str, object], expected: tuple[str, ...]) -> None:
    options = {"capabilities": _caps(), "variables": ("n",), "hypotheses": ("h", "j")}
    assert compile_action(action, **options) == expected
    assert compile_action(json.dumps(action), **options) == expected
    assert compile_action(json.dumps(action).encode("utf-8"), **options) == expected


def test_import_authority_and_every_command_are_checked_before_execution() -> None:
    action = _use("zero_add", "n")
    assert compile_action(action, capabilities=_caps(imports=("zero_add",)), variables=("n",)) == (
        "use zero_add", "specialize zero_add n", "apply zero_add",
    )
    with pytest.raises(ProtocolError):
        compile_action(action, capabilities=_caps(), variables=("n",))
    for missing in ("use", "specialize", "apply"):
        with pytest.raises(ProtocolError):
            compile_action(action, capabilities=_caps(imports=("zero_add",), commands=COMMANDS - {missing}), variables=("n",))
    # Local hypotheses do not need or silently grant library import authority.
    assert compile_action(_use("zero_add"), capabilities=_caps(), hypotheses=("zero_add",)) == ("apply zero_add",)


@pytest.mark.parametrize("authority", [
    SurfaceCapabilities(),
    SurfaceCapabilities(allowed_commands=frozenset({"refl"})),
    SurfaceCapabilities(allowed_theorems=frozenset()), None, {},
])
def test_unbounded_or_untyped_authority_is_rejected(authority: object) -> None:
    with pytest.raises(ProtocolError):
        compile_action(_dispatch("refl"), capabilities=authority)


@pytest.mark.parametrize("action", [
    {}, [], None, True,
    {"v": True, "op": "Witness", "term": "0"},
    {"v": 2, "op": "Witness", "term": "0"},
    {"v": 1, "op": "Unknown", "term": "0"},
    {"v": 1, "op": "Witness"},
    {"v": 1, "op": "Witness", "term": "0", "tactics": ["refl"]},
    _use("DNE"), _use("PA7"), _use("PA3", "0"), _use("unknown_lemma"),
    _use("h; refl"), _use("h", "n; refl"), _use("h", "m"),
    _use("h", *("0" for _ in range(17))),
    _action("Use", name="h", specializations="0"),
    _action("Witness", term="#0"), _action("Witness", term="?t0"),
    _action("Witness", term=0), _action("Witness", term="m"),
    _action("Witness", term="S 64"),
    _action("Cut", kind="assert", name="k", formula="n = n"),
    _action("Cut", kind="have", name="h", formula="n = n"),
    _action("Cut", kind="have", name="n", formula="n = n"),
    _action("Cut", kind="have", name="k", formula="m = m"),
    _action("Cut", kind="have", name="k", formula="n = n; refl"),
    _action("Induct", variable="n", motive="n = n"),
    _action("Induct", variable="m", motive="goal"),
    _action("Induct", variable="n; simp", motive="goal"),
    _action("Rewrite", source="not_here", direction="forward", location="goal"),
    _action("Rewrite", source="h", direction="both", location="goal"),
    _action("Rewrite", source="h", direction="forward", location="missing"),
    _action("Rewrite", source="h", direction="forward", location="goal; refl"),
    _split("and", "h"), _split("intro", "h"), _split("cases"), _split("cases", "missing"),
    _split("intro", "goal"),
    _dispatch("vampire"), _dispatch("ring"), _dispatch("auto"),
    _dispatch("simp", ["not_here"]), _dispatch("simp", ["h", "h"]),
    _dispatch("norm_num", ["h"]), _dispatch("refl", ["h"]),
    _action("Dispatch", solver="simp", premises=[], bounds={"max_calls": True}),
    _action("Dispatch", solver="simp", premises=[], bounds={"max_calls": 0}),
    _action("Dispatch", solver="simp", premises=[], bounds={"max_calls": 2}),
    _action("Dispatch", solver="simp", premises=[], bounds={"max_calls": 1, "max_seconds": 100}),
    _action("Dispatch", solver="simp", premises="h", bounds={"max_calls": 1}),
])
def test_bad_typed_actions_fail_closed(action: object) -> None:
    with pytest.raises(ProtocolError):
        compile_action(action, capabilities=_caps(), variables=("n",), hypotheses=("h",))


@pytest.mark.parametrize("source", [
    '{"v":1,"op":"Witness","term":"0","term":"1"}',
    '{"v":1,"v":1,"op":"Witness","term":"0"}',
    '{"v":1,"op":"Dispatch","solver":"refl","premises":[],"bounds":{"max_calls":1,"max_calls":1}}',
    '{"v":1.0,"op":"Witness","term":"0"}',
    '{"v":NaN,"op":"Witness","term":"0"}',
    '{"v":Infinity,"op":"Witness","term":"0"}',
    b'{"v":1,"op":"Witness","term":"\xff"}',
    '{"v":1,"op":"Witness","term":"' + "0" * 20000 + '"}',
    '[' * 2000 + '0' + ']' * 2000,
])
def test_raw_json_does_not_hide_duplicate_keys_nonfinite_values_or_nesting(source: object) -> None:
    with pytest.raises(ProtocolError):
        compile_action(source, capabilities=_caps())


def test_cyclic_already_decoded_json_is_bounded() -> None:
    record = _action("Witness", term="0")
    record["term"] = record
    with pytest.raises(ProtocolError):
        compile_action(record, capabilities=_caps())


@pytest.mark.parametrize(("variables", "hypotheses"), [
    ("n", ()), (("n", "n"), ()), (("n",), ("n",)), (("n; refl",), ()),
    (("S",), ()), (("PA1",), ()), (("n",), ("h", "h")),
    (tuple(f"n{i}" for i in range(17)), ()), ((), tuple(f"h{i}" for i in range(17))),
])
def test_scope_names_are_explicit_safe_distinct_and_bounded(variables: object, hypotheses: object) -> None:
    with pytest.raises(ProtocolError):
        compile_action(_dispatch("refl"), capabilities=_caps(), variables=variables, hypotheses=hypotheses)


def test_receipt_binds_normalized_action_complete_state_focus_context_and_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    goals = ("n : ℕ, h : n = n ⊢ n = n", "⊢ 0 = 0")
    kwargs = {"capabilities": _caps(), "goals": goals, "variables": ("n",), "hypotheses": ("h",)}
    action = _action("Cut", kind="have", name="k", formula="forall x. x = x")
    original = action_receipt(action, **kwargs)
    assert original["state_sha256"] == state_sha256(goals)
    assert original["environment_sha256"] == capability_sha256(_caps())
    assert original["action"]["formula"] == "∀ x. x = x"
    assert original["kernel_checked"] is False
    unhashed = dict(original)
    assert unhashed.pop("receipt_sha256") == _digest(unhashed)
    changed_tail = action_receipt(action, **{**kwargs, "goals": (goals[0], "⊢ 1 = 1")})
    changed_focus = action_receipt(action, **kwargs, focus=1)
    changed_order = action_receipt(action, **{**kwargs, "hypotheses": ("j", "h")})
    changed_authority = action_receipt(action, **{**kwargs, "capabilities": _caps(commands=COMMANDS - {"rewrite"})})
    profile = development_profile()
    profile["profile_sha256"] = "f" * 64
    monkeypatch.setattr(protocol, "development_profile", lambda: profile)
    changed_profile = action_receipt(action, **kwargs)
    assert len({entry["receipt_sha256"] for entry in (original, changed_tail, changed_focus, changed_order, changed_authority, changed_profile)}) == 6
    action["formula"] = "0 = 1"
    assert original["action"]["formula"] == "∀ x. x = x"


@pytest.mark.parametrize(("goals", "focus"), [
    ((), 0), (["⊢ 0 = 0"], 0), (("⊢ 0 = 0",), True), (("⊢ 0 = 0",), 1),
    (("⊢ 0 = 0\nrefl",), 0), (("⊢ 0 = 0\u202e",), 0), (("",), 0),
    (("⊢ 0 = 0",) * 65, 0), (("x" * 65537,), 0),
])
def test_invalid_receipt_state_is_rejected(goals: object, focus: object) -> None:
    with pytest.raises(ProtocolError):
        action_receipt(_dispatch("refl"), capabilities=_caps(), goals=goals, focus=focus)


@pytest.mark.parametrize(("source", "actions"), [
    ("forall n. n = n", [_split("intro", "n"), _dispatch("refl")]),
    ("forall n. exists m. m = n", [_split("intro", "n"), _action("Witness", term="n"), _dispatch("refl")]),
    ("0 = 0 /\\ 1 = 1", [_split("and"), _dispatch("refl"), _dispatch("refl")]),
    ("0 = 0 \\/ 0 = 1", [_split("left"), _dispatch("refl")]),
    ("0 = 1 \\/ 0 = 0", [_split("right"), _dispatch("refl")]),
    ("(0 = 0 /\\ 1 = 1) -> 0 = 0", [_split("intro", "h"), _split("cases", "h"), _dispatch("assumption")]),
    ("0 = 0", [_action("Cut", kind="have", name="h", formula="0 = 0"), _dispatch("refl"), _use("h")]),
    ("0 = 0", [_action("Cut", kind="suffices", name="h", formula="0 = 0"), _use("h"), _dispatch("refl")]),
    ("forall n. 0 + n = n", [_split("intro", "n"), _action("Induct", variable="n", motive="goal"), _dispatch("simp"), _dispatch("simp", ["IH"])]),
    ("forall n. n + 0 = n", [_split("intro", "n"), _use("PA3")]),
    ("forall n. S n = 0 -> bot", [_split("intro", "n"), _split("intro", "h"), _use("PA1"), _use("h")]),
    ("forall n m. n = m -> S n = S m", [_split("intro", "n"), _split("intro", "m"), _split("intro", "h"), _action("Rewrite", source="h", direction="forward", location="goal"), _dispatch("refl")]),
    ("2 + 3 = 5", [_dispatch("norm_num")]),
    ("forall n m. S n + m = S (n + m)", [_split("intro", "n"), _split("intro", "m"), _dispatch("compact_arith")]),
])
def test_actions_execute_on_native_surface_then_original_goal_is_kernel_checked(source: str, actions: list[dict[str, object]]) -> None:
    owner = _owner(source)
    transactions = []
    for action in actions:
        before = owner
        owner, receipt = execute_action(owner, action, capabilities=_caps())
        assert receipt["status"] == "applied"
        assert receipt["kernel_checked"] is False
        assert receipt["proposal"]["state_sha256"] == state_sha256(tuple(render_goals(before.state)))
        transactions.append(receipt["surface_transaction"])
    certificate = checked_final(owner.state, owner.original_target)
    assert check((), certificate, owner.original_target)
    replay = run_proof(source, transactions, capabilities=_caps())
    assert replay.kernel_checked is True


def test_multi_command_local_use_is_atomic_even_after_successful_prefix() -> None:
    caps = _caps()
    owner, _ = execute_action(_owner("(forall n. n = n) -> 0 = 0"), _split("intro", "h"), capabilities=caps)
    before_state, before_history, before_replay = owner.state, owner.state.history, owner.replay_steps
    records = owner.trace.record_count
    prefix = run_surface(owner, "specialize h 0", capabilities=caps, record_trace=False)
    assert prefix.state != before_state  # the prefix really succeeds and mutates the candidate
    with pytest.raises(TacticError, match="universal"):
        execute_action(owner, _use("h", "0", "0"), capabilities=caps)
    assert owner.state is before_state
    assert owner.state.history == before_history
    assert owner.replay_steps == before_replay
    assert owner.trace.record_count == records + 1
    assert owner.trace.last_record["status"] == "error"
    after, receipt = execute_action(owner, _use("h", "0"), capabilities=caps)
    assert after.state.is_done()
    assert len(after.state.history) == len(before_history) + 1
    assert receipt["proposal"]["commands"] == ["specialize h 0", "apply h"]
    assert check((), checked_final(after.state, after.original_target), after.original_target)


def test_multi_command_import_use_is_atomic_after_checked_import_and_specialization() -> None:
    caps = _caps(imports=("zero_add",))
    owner = _owner("0 + 0 = 0")
    before_state, before_history, before_replay = owner.state, owner.state.history, owner.replay_steps
    prefix = run_surface(owner, "use zero_add; specialize zero_add 0", capabilities=caps, record_trace=False)
    assert prefix.state != owner.state
    with pytest.raises(TacticError, match="universal"):
        execute_action(owner, _use("zero_add", "0", "0"), capabilities=caps)
    assert owner.state is before_state
    assert owner.state.history == before_history
    assert owner.replay_steps == before_replay
    assert not owner.state.current().context
    after, receipt = execute_action(owner, _use("zero_add", "0"), capabilities=caps)
    assert receipt["proposal"]["commands"] == ["use zero_add", "specialize zero_add 0", "apply zero_add"]
    assert check((), checked_final(after.state, after.original_target), after.original_target)


def test_use_macro_does_not_touch_preexisting_tail_goals() -> None:
    caps = _caps()
    owner = _owner("((forall n. n = n) -> 0 = 0) /\\ 1 = 1")
    owner, _ = execute_action(owner, _split("and"), capabilities=caps)
    owner, _ = execute_action(owner, _split("intro", "h"), capabilities=caps)
    tail = owner.state.goals[1:]
    after, _ = execute_action(owner, _use("h", "0"), capabilities=caps)
    assert after.state.goals == tail
    after, _ = execute_action(after, _dispatch("refl"), capabilities=caps)
    assert check((), checked_final(after.state, after.original_target), after.original_target)


def test_executor_rejects_classical_mismatched_and_closed_sessions_before_tactics() -> None:
    owner = _owner("0 = 0")
    for altered in (replace(owner, classical=True), replace(owner, target_source="0 = 1"), replace(owner, original_names=("n",))):
        with pytest.raises(ProtocolError):
            execute_action(altered, _dispatch("refl"), capabilities=_caps())
        assert altered.trace.record_count == 0
    after, _ = execute_action(owner, _dispatch("refl"), capabilities=_caps())
    with pytest.raises(ProtocolError, match="no open goal"):
        execute_action(after, _dispatch("refl"), capabilities=_caps())


def test_native_failure_is_not_a_negative_theoremhood_result() -> None:
    owner = _owner("0 = 1")
    before = owner.state
    with pytest.raises(TacticError):
        execute_action(owner, _dispatch("refl"), capabilities=_caps())
    assert owner.state is before
    assert not owner.state.history
    assert owner.trace.last_record["status"] == "error"
    assert "qed" not in owner.trace.last_record


def test_profile_source_cache_is_detached_and_detects_source_identity_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source.py"
    source.write_bytes(b"first source\n")
    monkeypatch.setattr(protocol, "_ROOT", tmp_path)
    monkeypatch.setattr(protocol, "_SOURCE_PATHS", ("source.py",))
    first = development_profile()
    source.write_bytes(b"second, different source\n")
    second = development_profile()
    assert first["profile_sha256"] != second["profile_sha256"]
    assert first["source_bindings"][0]["sha256"] == hashlib.sha256(b"first source\n").hexdigest()
    alias = tmp_path / "alias.py"
    alias.symlink_to(source)
    monkeypatch.setattr(protocol, "_SOURCE_PATHS", ("alias.py",))
    with pytest.raises(ProtocolError, match="regular file"):
        development_profile()
