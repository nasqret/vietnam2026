"""H0.3 canonical typed macro transport and deterministic compilation."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.ui.prove import (  # noqa: E402
    MAX_INPUT,
    SurfaceCapabilities,
    surface_transaction_name,
)
import training.peano_hydra.macros as macro_module  # noqa: E402
from training.peano_hydra.macros import (  # noqa: E402
    MACRO_FORMAT,
    MACRO_PROTOCOL_DOCUMENT_SHA256,
    MACRO_PROTOCOL_FORMAT,
    MACRO_PROTOCOL_ID,
    MACRO_PROTOCOL_PATH,
    MACRO_PROTOCOL_SEMANTIC_SHA256,
    MACRO_PROTOCOL_VERSION,
    MACRO_VERSION,
    MAX_DISPATCH_MEMORY_BYTES,
    MAX_DISPATCH_CALL_BYTES,
    MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES,
    MAX_DISPATCH_OUTPUT_BYTES,
    MAX_DISPATCH_PREMISES,
    MAX_DISPATCH_STEPS,
    MAX_DISPATCH_WALL_TIME_MS,
    MAX_MACRO_BYTES,
    MAX_SPECIALIZATIONS,
    CompiledMacro,
    Cut,
    Dispatch,
    DispatchBounds,
    DispatchRequest,
    Induct,
    MacroCompileError,
    MacroProtocolError,
    Rewrite,
    Split,
    Use,
    Witness,
    compile_macro,
    load_macro_protocol,
    macro_object,
    macro_protocol_identity,
    macro_sha256,
    parse_macro,
    serialize_macro,
)


BOUNDS = DispatchBounds(
    max_steps=10_000,
    max_wall_time_ms=2_000,
    max_memory_bytes=256 * 1024 * 1024,
    max_output_bytes=1_000_000,
)


ALL_ACTIONS = (
    Use("add_comm", ("n", "S m")),
    Cut("have", "h", "n + 0 = n"),
    Cut("suffices", "enough", "∃ x. n = x"),
    Witness("n + S m"),
    Induct("n", "∃ x. n · (n + 1) = 2 · x"),
    Rewrite("IH", "forward", None),
    Rewrite("add_comm", "backward", "h"),
    Split("conjunction"),
    Split("left"),
    Split("right"),
    Dispatch("vampire", ("add_comm", "IH"), BOUNDS),
)


def _wire(**changes: object) -> str:
    value: dict[str, object] = {
        "format": MACRO_FORMAT,
        "v": MACRO_VERSION,
        "action": "Witness",
        "term": "n",
    }
    value.update(changes)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def test_all_seven_action_types_round_trip_to_one_canonical_wire_form() -> None:
    for action in ALL_ACTIONS:
        encoded = serialize_macro(action)
        assert parse_macro(encoded) == action
        assert parse_macro(encoded.encode("utf-8")) == action
        assert serialize_macro(parse_macro("  " + encoded + "\n")) == encoded
        assert len(encoded.encode("utf-8")) <= MAX_MACRO_BYTES
        assert len(macro_sha256(action)) == 64


def test_use_encoding_and_digest_are_pinned() -> None:
    action = Use("add_comm", ("n", "S m"))
    assert serialize_macro(action) == (
        '{"action":"Use","format":"peano-hydra-macro","name":"add_comm",'
        '"specializations":["n","S m"],"v":1}'
    )
    assert macro_sha256(action) == (
        "f55e72eb782eb7aeddb5ce722085bc984c64590ff95e0d41be9e6ce6ffe84628"
    )
    detached = macro_object(action)
    detached["name"] = "forged"
    assert macro_object(action)["name"] == "add_comm"


def test_machine_readable_protocol_and_both_hashes_are_pinned() -> None:
    assert MACRO_PROTOCOL_DOCUMENT_SHA256 == (
        "6f6920d2d952251170733674a3af8da09926f4faf19215317a32bc0317d4a482"
    )
    assert MACRO_PROTOCOL_SEMANTIC_SHA256 == (
        "b5fef1ea1b85251ab7f0b8c111cb37e789f96f20771665b4f0dc8b746400552c"
    )
    protocol = load_macro_protocol()
    assert protocol["format"] == MACRO_PROTOCOL_FORMAT
    assert protocol["v"] == MACRO_PROTOCOL_VERSION
    assert protocol["id"] == MACRO_PROTOCOL_ID
    assert set(protocol["transport"]["actions"]) == {  # type: ignore[index]
        "Use",
        "Cut",
        "Witness",
        "Induct",
        "Rewrite",
        "Split",
        "Dispatch",
    }
    actions = protocol["transport"]["actions"]  # type: ignore[index]
    assert actions["Rewrite"]["compilation"]["command_templates"] == [
        "rewrite {source}",
        "rewrite <- {source}",
        "rewrite {source} at {location}",
        "rewrite <- {source} at {location}",
    ]
    assert actions["Dispatch"]["compilation"] == {
        "channel": "untrusted-dispatch-reconstruction",
        "command_heads": [],
        "reconstruction_required": True,
        "status_authority": False,
    }
    assert protocol["limits"]["max_dispatch_call_bytes"] == MAX_DISPATCH_CALL_BYTES  # type: ignore[index]
    assert protocol["limits"]["max_dispatch_output_evidence_bytes"] == (  # type: ignore[index]
        MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES
    )
    assert MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES == MAX_DISPATCH_OUTPUT_BYTES + 1
    resources = protocol["dispatch_subprocess"]["host"]["resource_semantics"]  # type: ignore[index]
    assert resources["steps_used"] == {
        "authority": "untrusted-adapter-self-report",
        "host_enforced": False,
        "accepted_relation": (
            "not-less-than-public-command-count-and-"
            "not-greater-than-request-max_steps"
        ),
        "campaign_usage_metric_eligible": False,
    }
    assert resources["memory_enforcement_modes"][  # type: ignore[index]
        "linux-rlimit-as-data+sampled-leader-rss"
    ]["campaign_host_eligible"] is True
    assert resources["memory_enforcement_modes"][  # type: ignore[index]
        "darwin-sampled-leader-rss-only"
    ]["campaign_host_eligible"] is False
    raw = MACRO_PROTOCOL_PATH.read_bytes()
    semantic = json.dumps(
        protocol,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert hashlib.sha256(raw).hexdigest() == MACRO_PROTOCOL_DOCUMENT_SHA256
    assert hashlib.sha256(semantic).hexdigest() == MACRO_PROTOCOL_SEMANTIC_SHA256
    assert macro_protocol_identity() == {
        "format": MACRO_PROTOCOL_FORMAT,
        "v": MACRO_PROTOCOL_VERSION,
        "id": MACRO_PROTOCOL_ID,
        "semantic_sha256": MACRO_PROTOCOL_SEMANTIC_SHA256,
        "document_sha256": MACRO_PROTOCOL_DOCUMENT_SHA256,
    }


def test_protocol_loader_fails_closed_on_document_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    changed = tmp_path / "macro-protocol-v1.json"
    changed.write_bytes(MACRO_PROTOCOL_PATH.read_bytes() + b" ")
    monkeypatch.setattr(macro_module, "MACRO_PROTOCOL_PATH", changed)
    with pytest.raises(MacroProtocolError, match="document SHA-256 drift"):
        load_macro_protocol()


def test_protocol_loader_fails_closed_on_live_constant_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(macro_module, "MAX_SPECIALIZATIONS", 33)
    with pytest.raises(MacroProtocolError, match="live v1 contract"):
        load_macro_protocol()


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (Use("add_comm"), ("use add_comm",)),
        (
            Use("add_comm", ("n", "S m")),
            (
                "use add_comm",
                "specialize add_comm n",
                "specialize add_comm S m",
            ),
        ),
        (Cut("have", "h", "n = n"), ("have h : n = n",)),
        (Cut("suffices", "h", "n = n"), ("suffices h : n = n",)),
        (Witness("n + 1"), ("exists n + 1",)),
        (Induct("n", "n + 0 = n"), ("induction n",)),
        (Rewrite("h", "forward"), ("rewrite h",)),
        (Rewrite("h", "backward"), ("rewrite <- h",)),
        (Rewrite("h", "forward", "h2"), ("rewrite h at h2",)),
        (Rewrite("h", "backward", "h2"), ("rewrite <- h at h2",)),
        (Split("conjunction"), ("split",)),
        (Split("left"), ("left",)),
        (Split("right"), ("right",)),
    ],
)
def test_structured_actions_compile_only_to_documented_public_commands(
    action: object,
    expected: tuple[str, ...],
) -> None:
    result = compile_macro(action)  # type: ignore[arg-type]
    assert result == CompiledMacro(action, expected, None)
    assert result.action is action or result.action == action
    assert result.dispatch is None
    for command in result.public_commands:
        assert surface_transaction_name(command, False) is not None
        assert command.split(" ", 1)[0] not in {
            "auto",
            "compact_arith",
            "norm_num",
            "qed",
            "ring",
        }


def test_induction_motive_is_retained_but_not_smuggled_into_public_syntax() -> None:
    action = Induct("n", "∃ x. n · (n + 1) = 2 · x")
    compiled = compile_macro(action)

    assert compiled.public_commands == ("induction n",)
    assert compiled.action == action
    assert compiled.action.motive == "∃ x. n · (n + 1) = 2 · x"


def test_dispatch_is_a_separate_untrusted_channel_with_all_bounds_retained() -> None:
    action = Dispatch("vampire", ("add_comm", "IH"), BOUNDS)
    with pytest.raises(MacroCompileError, match="not registered"):
        compile_macro(action)

    compiled = compile_macro(action, available_solvers={"vampire", "native"})
    assert compiled.public_commands == ()
    assert compiled.action == action
    assert compiled.dispatch == DispatchRequest("vampire", ("add_comm", "IH"), BOUNDS)
    assert compiled.dispatch.authority == "untrusted-hints-reconstruction-required"
    assert not hasattr(compiled.dispatch, "proved")
    assert not hasattr(compiled.dispatch, "certificate")


@pytest.mark.parametrize(
    "source",
    [
        "[]",
        "null",
        "NaN",
        _wire(format="wrong"),
        _wire(v=2),
        _wire(v=True),
        _wire(action="Exact"),
        '{"action":"Witness","format":"peano-hydra-macro",'
        '"term":"n","term":"m","v":1}',
        '{"action":"Dispatch","bounds":{"max_memory_bytes":1,'
        '"max_memory_bytes":2,"max_output_bytes":1,"max_steps":1,'
        '"max_wall_time_ms":1},"format":"peano-hydra-macro",'
        '"premises":[],"solver":"native","v":1}',
    ],
)
def test_parser_rejects_non_json_duplicates_unknown_versions_and_actions(
    source: str,
) -> None:
    with pytest.raises(MacroProtocolError):
        parse_macro(source)


def test_parser_rejects_missing_and_additional_fields_at_every_object_level() -> None:
    missing = json.loads(_wire())
    del missing["term"]
    with pytest.raises(MacroProtocolError, match="missing 'term'"):
        parse_macro(json.dumps(missing))

    with pytest.raises(MacroProtocolError, match="additional 'command'"):
        parse_macro(_wire(command="refl"))

    dispatch = macro_object(Dispatch("native", (), BOUNDS))
    dispatch["bounds"]["secret"] = 1  # type: ignore[index]
    with pytest.raises(MacroProtocolError, match="additional 'secret'"):
        parse_macro(json.dumps(dispatch))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Witness("n * 1"),
        lambda: Witness("01"),
        lambda: Cut("have", "h", "forall n. n = n"),
        lambda: Cut("have", "h", "n <= n"),
        lambda: Witness("#0"),
        lambda: Witness("257"),
        lambda: Cut("have", "h", "n = n\nm = m"),
    ],
)
def test_profile_surface_guards_reject_noncanonical_or_out_of_profile_payloads(
    factory,
) -> None:
    with pytest.raises(MacroProtocolError):
        factory()


def test_parser_requires_json_arrays_for_repeated_fields() -> None:
    use = macro_object(Use("add_comm"))
    use["specializations"] = "n"
    with pytest.raises(MacroProtocolError, match="JSON array"):
        parse_macro(json.dumps(use))

    dispatch = macro_object(Dispatch("native", (), BOUNDS))
    dispatch["premises"] = "add_comm"
    with pytest.raises(MacroProtocolError, match="JSON array"):
        parse_macro(json.dumps(dispatch))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Cut("lemma", "h", "n = n"),
        lambda: Rewrite("h", "reverse"),
        lambda: Rewrite("h", "forward", 3),
        lambda: Split("cases"),
        lambda: Use("S"),
        lambda: Induct("n m", "n = n"),
        lambda: Dispatch("Vampire", (), BOUNDS),
        lambda: Dispatch("native", ("h", "h"), BOUNDS),
    ],
)
def test_exact_enums_names_and_types_reject_hidden_surface_syntax(factory) -> None:
    with pytest.raises(MacroProtocolError):
        factory()


@pytest.mark.parametrize(
    ("field", "value", "maximum"),
    [
        ("max_steps", 0, MAX_DISPATCH_STEPS),
        ("max_steps", True, MAX_DISPATCH_STEPS),
        ("max_steps", MAX_DISPATCH_STEPS + 1, MAX_DISPATCH_STEPS),
        ("max_wall_time_ms", 0, MAX_DISPATCH_WALL_TIME_MS),
        (
            "max_wall_time_ms",
            MAX_DISPATCH_WALL_TIME_MS + 1,
            MAX_DISPATCH_WALL_TIME_MS,
        ),
        ("max_memory_bytes", 0, MAX_DISPATCH_MEMORY_BYTES),
        (
            "max_memory_bytes",
            MAX_DISPATCH_MEMORY_BYTES + 1,
            MAX_DISPATCH_MEMORY_BYTES,
        ),
        ("max_output_bytes", 0, MAX_DISPATCH_OUTPUT_BYTES),
        (
            "max_output_bytes",
            MAX_DISPATCH_OUTPUT_BYTES + 1,
            MAX_DISPATCH_OUTPUT_BYTES,
        ),
    ],
)
def test_dispatch_bounds_are_positive_exact_integers_under_protocol_caps(
    field: str,
    value: object,
    maximum: int,
) -> None:
    data = {
        "max_steps": 1,
        "max_wall_time_ms": 1,
        "max_memory_bytes": 1,
        "max_output_bytes": 1,
    }
    data[field] = value
    with pytest.raises(MacroProtocolError, match=str(maximum)):
        DispatchBounds(**data)  # type: ignore[arg-type]


def test_collection_and_wire_bounds_are_enforced_before_compilation() -> None:
    with pytest.raises(MacroProtocolError, match=str(MAX_SPECIALIZATIONS)):
        Use("add_comm", ("n",) * (MAX_SPECIALIZATIONS + 1))
    premises = tuple(f"h{index}" for index in range(MAX_DISPATCH_PREMISES + 1))
    with pytest.raises(MacroProtocolError, match=str(MAX_DISPATCH_PREMISES)):
        Dispatch("native", premises, BOUNDS)
    with pytest.raises(MacroProtocolError, match=str(MAX_MACRO_BYTES)):
        parse_macro(" " * (MAX_MACRO_BYTES + 1))


def test_typed_helpers_reject_lazy_iterables_without_consuming_them() -> None:
    assert Use("add_comm", ["n"]).specializations == ("n",)  # type: ignore[arg-type]
    assert Dispatch("native", ["h"], BOUNDS).premises == ("h",)  # type: ignore[arg-type]

    terms = itertools.repeat("n")
    with pytest.raises(MacroProtocolError, match="exact tuple or list"):
        Use("add_comm", terms)  # type: ignore[arg-type]
    assert next(terms) == "n"

    premises = itertools.repeat("h")
    with pytest.raises(MacroProtocolError, match="exact tuple or list"):
        Dispatch("native", premises, BOUNDS)  # type: ignore[arg-type]
    assert next(premises) == "h"

    solvers = itertools.repeat("native")
    with pytest.raises(MacroCompileError, match="exact tuple, list, set"):
        compile_macro(  # type: ignore[arg-type]
            Dispatch("native", (), BOUNDS),
            available_solvers=solvers,
        )
    assert next(solvers) == "native"


def test_compilation_rejects_unknown_or_masked_theorems_and_commands() -> None:
    with pytest.raises(MacroCompileError, match="no checked public theorem"):
        compile_macro(Use("invented_lemma"))

    use_only = SurfaceCapabilities(
        label="macro-use-only",
        allowed_commands=frozenset({"use"}),
        allowed_theorems=frozenset({"add_comm"}),
    )
    assert compile_macro(Use("add_comm"), capabilities=use_only).public_commands == (
        "use add_comm",
    )
    with pytest.raises(MacroCompileError, match="specialize"):
        compile_macro(Use("add_comm", ("n",)), capabilities=use_only)

    rewrite_only = SurfaceCapabilities(
        label="macro-rewrite-only",
        allowed_commands=frozenset({"rewrite"}),
        allowed_theorems=frozenset(),
    )
    with pytest.raises(MacroCompileError, match="induction"):
        compile_macro(Induct("n", "n = n"), capabilities=rewrite_only)


def test_compiler_rejects_a_surface_line_that_would_exceed_public_input_limit() -> None:
    # A canonical formula can independently occupy MAX_INPUT characters; the
    # command prefix must still fit the stricter complete-line public bound.
    name_length = (MAX_INPUT - len(" = ")) // 2
    variable = "n" * name_length
    formula = f"{variable} = {variable}"
    assert len(formula) <= MAX_INPUT
    action = Cut("have", "h", formula)
    assert len(serialize_macro(action)) < MAX_MACRO_BYTES
    with pytest.raises(MacroCompileError, match="surface limit"):
        compile_macro(action)


def test_macro_transport_has_no_certificate_or_kernel_acceptance_channel() -> None:
    for action in ALL_ACTIONS:
        encoded = macro_object(action)
        assert "certificate" not in encoded
        assert "kernel_accepted" not in encoded
        assert "proved" not in encoded
