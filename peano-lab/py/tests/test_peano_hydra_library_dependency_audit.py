"""Focused adversarial contracts for the candidate-only A2.1 audit."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import training.peano_hydra.library_dependency_audit as audit_module  # noqa: E402
import peano_lab.library.candidate_validation as candidate_module  # noqa: E402
from peano_lab.engine.tactics import TacticLimit  # noqa: E402
from peano_lab.library.candidate_validation import CandidateBodyError  # noqa: E402
from peano_lab.library.theorems import TheoremSpec  # noqa: E402


CLI_PATH = ROOT / "scripts" / "build_peano_hydra_library_dependency_audit.py"
RETAINED = ROOT / "artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json"
RETAINED_BYTES = 4_188_048
RETAINED_SHA256 = "4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040"
RETAINED_ROOT = "12166de8fb0cc028c3b026deb939418a19f001ff8342acab479d433e15d3a83e"
RETAINED_RECORD_ROOT = (
    "8ae5553e79b15c4e83a76e1eab92cb0983539fa913dfe2bec29d0fb17fb7d784"
)


def _load_cli():
    specification = importlib.util.spec_from_file_location(
        "_test_peano_hydra_dependency_audit_cli", CLI_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _spec(
    name: str,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
) -> TheoremSpec:
    return TheoremSpec(
        name,
        "forall n. n = n",
        dependencies,
        script,
        "Fixture theorem.",
    )


def _core(*specs: TheoremSpec) -> dict[str, TheoremSpec]:
    return {spec.name: spec for spec in specs}


def test_fixture_removes_only_kernel_accepted_omissions() -> None:
    unused = _spec("unused", (), ("intro n", "refl"))
    used = _spec("used", (), ("intro n", "refl"))
    theorem = _spec(
        "consumer",
        (unused.name, used.name),
        ("exact used",),
    )

    result = audit_module._audit_spec(theorem, core=_core(unused, used))

    assert result["initial_dependencies"] == ["unused", "used"]
    assert result["candidate_dependencies"] == ["used"]
    assert result["complete"] is True
    assert result["positive_receipt"]["kernel_accepted"] is True
    attempts = result["attempts"]
    assert [(row["pass_index"], row["omitted_dependency"], row["outcome"]) for row in attempts] == [
        (0, "used", "exact-recipe-rejected"),
        (0, "unused", "kernel-accepted"),
        (1, "used", "exact-recipe-rejected"),
    ]
    assert attempts[0]["failure"]["phase"] == "command"
    assert attempts[1]["failure"] is None
    assert attempts[1]["positive_receipt"]["kernel_accepted"] is True
    assert attempts[-1]["after_dependencies"] == ["used"]


def test_reverse_order_fixed_point_is_deterministic_and_content_addressed() -> None:
    first = _spec("first", (), ("intro n", "refl"))
    second = _spec("second", (), ("intro n", "refl"))
    theorem = _spec(
        "consumer",
        (first.name, second.name),
        ("intro n", "refl"),
    )
    core = _core(first, second)

    left = audit_module._audit_spec(theorem, core=core)
    right = audit_module._audit_spec(theorem, core=core)

    assert left == right
    assert left["candidate_dependencies"] == []
    assert [row["omitted_dependency"] for row in left["attempts"]] == [
        "second",
        "first",
    ]
    for index, attempt in enumerate(left["attempts"]):
        assert attempt["attempt_index"] == index
        payload = {key: value for key, value in attempt.items() if key != "record_sha256"}
        assert attempt["record_sha256"] == hashlib.sha256(
            audit_module._compact_bytes(payload)
        ).hexdigest()


def test_readable_and_submitted_route_receipts_are_domain_separated() -> None:
    dependency = _spec("dependency", (), ("intro n", "refl"))
    theorem = _spec("consumer", (dependency.name,), ("exact dependency",))
    recipe = audit_module._audit_spec(theorem, core=_core(dependency))

    readable = audit_module._route_receipt(recipe, route="readable-proof")
    submitted = audit_module._route_receipt(
        recipe, route="submitted-construction-candidate"
    )

    assert readable["dependencies"] == submitted["dependencies"] == ["dependency"]
    assert readable["preimage"]["recipe_audit_sha256"] == recipe["receipt_sha256"]
    assert submitted["preimage"]["recipe_audit_sha256"] == recipe["receipt_sha256"]
    assert readable["sha256"] != submitted["sha256"]


def test_independent_kernel_rejection_blocks_positive_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theorem = _spec("reflexive", (), ("intro n", "refl"))
    compilation = audit_module.compile_candidate_body(theorem, core={})
    monkeypatch.setattr(audit_module, "check", lambda *_args: False)

    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="independent kernel rejected",
    ):
        audit_module._body_receipt(compilation)


def test_injected_internal_omission_failure_is_unknown_and_blocks_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependency = _spec("dependency", (), ("intro n", "refl"))
    theorem = _spec("consumer", (dependency.name,), ("exact dependency",))
    original = audit_module.compile_candidate_body

    def injected(spec: TheoremSpec, *, core):
        if not spec.dependencies:
            try:
                raise TypeError("injected internal failure")
            except TypeError as cause:
                raise CandidateBodyError("wrapped internal failure") from cause
        return original(spec, core=core)

    monkeypatch.setattr(audit_module, "compile_candidate_body", injected)

    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="failed internally; result is unknown",
    ):
        audit_module._audit_spec(theorem, core=_core(dependency))


def test_injected_resource_limit_is_unknown_and_blocks_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependency = _spec("dependency", (), ("intro n", "refl"))
    theorem = _spec("consumer", (dependency.name,), ("exact dependency",))
    original = audit_module.compile_candidate_body

    def injected(spec: TheoremSpec, *, core):
        if not spec.dependencies:
            try:
                raise TacticLimit("injected limit")
            except TacticLimit as cause:
                raise CandidateBodyError(
                    "wrapped limit",
                    phase="command",
                    kind="resource-limit",
                    command_index=0,
                    command="exact dependency",
                ) from cause
        return original(spec, core=core)

    monkeypatch.setattr(audit_module, "compile_candidate_body", injected)

    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="resource limit; result is unknown",
    ):
        audit_module._audit_spec(theorem, core=_core(dependency))


def test_live_final_certificate_limit_is_structured_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theorem = _spec("reflexive", (), ("intro n", "refl"))

    def injected(_proof):
        raise TacticLimit("injected live proof bound")

    monkeypatch.setattr(candidate_module, "enforce_live_proof_bounds", injected)
    with pytest.raises(CandidateBodyError) as raised:
        audit_module.compile_candidate_body(theorem, core={})
    assert raised.value.phase == "finalization"
    assert raised.value.kind == "resource-limit"
    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="resource limit; result is unknown",
    ):
        audit_module._deterministic_failure(raised.value)


def test_canonical_encoder_rejects_floats_cycles_and_boolean_limits() -> None:
    with pytest.raises(audit_module.LibraryDependencyAuditError, match="unsupported"):
        audit_module.canonical_document_bytes({"x": 1.5})
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(audit_module.LibraryDependencyAuditError, match="cycle"):
        audit_module.canonical_document_bytes(cyclic)
    with pytest.raises(TypeError, match="positive integer"):
        audit_module.canonical_document_bytes({}, limit=True)


def test_strict_decoder_rejects_duplicate_keys_floats_and_noncanonical_bytes() -> None:
    with pytest.raises(audit_module.LibraryDependencyAuditError, match="duplicate"):
        audit_module._decode_document(b'{"x":1,"x":2}\n', "fixture", limit=100)
    with pytest.raises(audit_module.LibraryDependencyAuditError, match="floating"):
        audit_module._decode_document(b'{"x":1.5}\n', "fixture", limit=100)
    with pytest.raises(audit_module.LibraryDependencyAuditError, match="not canonical"):
        audit_module._decode_document(b'{"x":1}\n', "fixture", limit=100)


def test_public_surface_contains_no_authority_or_fast_path() -> None:
    assert set(audit_module.__all__) == {
        "DEPENDENCY_AUDIT_SCHEMA_FORMAT",
        "DEPENDENCY_AUDIT_SCHEMA_ID",
        "DEPENDENCY_AUDIT_SCHEMA_PATH",
        "DEPENDENCY_AUDIT_SCHEMA_SHA256",
        "DEPENDENCY_AUDIT_SCHEMA_VERSION",
        "LibraryDependencyAuditError",
        "build_candidate_dependency_audit",
        "canonical_document_bytes",
        "dependency_audit_schema",
        "dependency_audit_schema_identity",
        "load_dependency_audit",
        "validate_dependency_audit",
    }
    assert not any(
        name in audit_module.__all__
        for name in ("freeze", "publish", "minimal", "best_known", "fast_validate")
    )


def test_schema_source_is_strict_json_without_duplicate_keys() -> None:
    raw = audit_module.DEPENDENCY_AUDIT_SCHEMA_PATH.read_bytes()
    assert len(raw) == 34_247
    assert hashlib.sha256(raw).hexdigest() == (
        "ee6eb4daf48fbf320e79a54065befed758ff33c5251ec4a2c18b8093c349c0ff"
    )
    decoded = json.loads(raw, object_pairs_hook=audit_module._strict_object)
    assert type(decoded) is dict
    assert audit_module._sha256_json(
        decoded, limit=audit_module.MAX_SCHEMA_BYTES
    ) == audit_module.DEPENDENCY_AUDIT_SCHEMA_SHA256 == (
        "54d6b5128067b1f93d8f7393e0730d7da3a4ac838a0b55b6b6fe0ce92a0d4bc4"
    )
    assert decoded["constants"] == {
        "evaluation_eligible": False,
        "freeze_ready": False,
        "logic_mode": "intuitionistic",
        "minimality_claim": False,
        "optimized_best_known": False,
        "publication_ready": False,
        "retrieval_eligible": False,
        "status": "candidate",
        "training_eligible": False,
    }
    assert decoded["fixed_inputs"]["dependency_compiler"] == {
        "callable": "peano_lab.library.candidate_validation.compile_candidate_body",
        "source_count": 20,
        "source_root_sha256": audit_module.COMPILER_SOURCE_ROOT_SHA256,
        "v": 1,
    }
    for shape in decoded["object_shapes"].values():
        assert set(shape) == {"fields", "types"}
        assert set(shape["fields"]) == set(shape["types"])


def test_retained_candidate_sidecar_has_exact_two_pass_identity() -> None:
    raw = RETAINED.read_bytes()
    assert len(raw) == RETAINED_BYTES
    assert hashlib.sha256(raw).hexdigest() == RETAINED_SHA256
    value = audit_module._decode_document(
        raw, "retained dependency audit", limit=audit_module.MAX_AUDIT_BYTES
    )

    assert value["root_sha256"] == RETAINED_ROOT
    assert value["theorem_records"]["root_sha256"] == RETAINED_RECORD_ROOT
    assert value["aggregate"] == {
        "accepted_omission_observations": 3,
        "candidate_dependency_edges": 1_035,
        "declared_dependency_edges": 1_038,
        "exact_recipe_rejection_observations": 1_057,
        "requires_certificate_rebuild_count": 3,
        "theorem_count": 384,
        "unknown_observations": 0,
    }
    assert all(
        value[field] is False
        for field in (
            "evaluation_eligible",
            "freeze_ready",
            "minimality_claim",
            "optimized_best_known",
            "publication_ready",
            "retrieval_eligible",
            "training_eligible",
        )
    )
    reduced = {
        row["name"]: tuple(
            dependency
            for dependency in row["declared_dependencies"]
            if dependency not in row["recipe_audit"]["candidate_dependencies"]
        )
        for row in value["theorems"]
        if row["requires_certificate_rebuild"] is True
    }
    assert reduced == {
        "odd_add_odd": ("add_succ_left",),
        "finite_bounded_injective_surjective": ("beta_at_unique",),
        "beta_product_swap_last_invariant": ("le_refl",),
    }


def test_route_or_attempt_mutation_changes_every_binding_hash() -> None:
    dependency = _spec("dependency", (), ("intro n", "refl"))
    theorem = _spec("consumer", (dependency.name,), ("exact dependency",))
    recipe = audit_module._audit_spec(theorem, core=_core(dependency))
    mutated = deepcopy(recipe)
    mutated["attempts"][0]["failure"]["message_sha256"] = "0" * 64

    assert mutated["attempts"][0]["record_sha256"] != audit_module._record_hash(
        mutated["attempts"][0]
    )
    assert recipe["attempt_records"]["root_sha256"] == hashlib.sha256(
        audit_module._compact_bytes(recipe["attempt_records"]["preimage"])
    ).hexdigest()


def test_cli_publication_is_create_only_atomic_and_exact(tmp_path: Path) -> None:
    cli = _load_cli()
    destination = tmp_path / "audit.json"
    raw = b'{"fixture":true}\n'

    cli._publish(destination, raw)

    metadata = destination.lstat()
    assert stat.S_ISREG(metadata.st_mode)
    assert not stat.S_ISLNK(metadata.st_mode)
    assert destination.read_bytes() == raw
    cli._read_exact(destination, raw)
    with pytest.raises(audit_module.LibraryDependencyAuditError, match="already exists"):
        cli._publish(destination, b"replacement\n")
    assert destination.read_bytes() == raw


def test_cli_publish_race_preserves_foreign_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    destination = tmp_path / "audit.json"
    sentinel = b"foreign-writer\n"
    real_link = os.link

    def raced_link(source, target, *, follow_symlinks=False):
        Path(target).write_bytes(sentinel)
        return real_link(source, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(cli.os, "link", raced_link)
    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="cannot publish output document",
    ):
        cli._publish(destination, b"candidate\n")

    assert destination.read_bytes() == sentinel
    assert not tuple(tmp_path.glob(".audit.json.*.tmp"))


def test_loader_and_cli_reject_symlinked_ancestors(tmp_path: Path) -> None:
    cli = _load_cli()
    actual = tmp_path / "actual"
    actual.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    destination = linked / "audit.json"
    destination.write_bytes(b"{}\n")

    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="parent contains a link",
    ):
        cli._read_exact(destination, b"{}\n")
    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="parent contains a link",
    ):
        audit_module._safe_file(destination, label="fixture", limit=100)


def test_fixed_loader_accepts_the_exact_retained_input_envelopes() -> None:
    explicit, replay, table, inputs = audit_module._load_inputs(ROOT)

    assert len(explicit) == len(replay) == len(table) == 384
    assert sum(len(spec.dependencies) for spec in table.values()) == 1_038
    assert inputs["replay_pack"]["replay_report_artifact_sha256"] == (
        audit_module.REPLAY_REPORT_ARTIFACT_SHA256
    )


def test_fixed_loader_rejects_runtime_callable_origin_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(audit_module, "check", lambda *_args: True)

    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="runtime callable identity drifted",
    ):
        audit_module._load_inputs(ROOT)


def test_fixed_loader_independently_binds_documentation_member_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = audit_module._safe_file

    def tampered(path: Path, *, label: str, limit: int) -> bytes:
        raw = original(path, label=label, limit=limit)
        if label == "selected documentation 'explicit.json'":
            value = json.loads(raw)
            value["theorems"][0]["summary"] += " tampered"
            return audit_module.canonical_document_bytes(value, limit=limit)
        return raw

    monkeypatch.setattr(audit_module, "_safe_file", tampered)
    with pytest.raises(
        audit_module.LibraryDependencyAuditError,
        match="explicit.json.*bytes drifted",
    ):
        audit_module._load_inputs(ROOT)


def test_fresh_import_does_not_load_legacy_candidate_stacks() -> None:
    code = """
import sys
import training.peano_hydra.library_dependency_audit
forbidden = [
    name for name in sys.modules
    if 'quadratic_reciprocity_stack' in name
    or name.rsplit('.', 1)[-1].endswith('_candidate')
]
if forbidden:
    raise SystemExit(repr(sorted(forbidden)))
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT / "peano-lab" / "py"), str(ROOT))
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
