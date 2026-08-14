"""Focused adversarial contracts for the bounded A2.3d Cut-liveness pilot.

The producer and verifier deliberately implement the same scientific
transformation over different representations.  These tests keep the small
binder and filesystem boundaries synthetic; the one retained ``odd_add_odd``
build is exercised only by the bounded integration tests near the end.
"""

from __future__ import annotations

import ast
import base64
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
for source_root in (ROOT / "peano-lab/py", ROOT):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from peano_lab.kernel.artifact_codec import (  # noqa: E402
    decode_artifact,
    encode_proof,
)
from peano_lab.kernel.checker import check  # noqa: E402
from peano_lab.kernel.formulas import And, Eq, Exists, Forall  # noqa: E402
from peano_lab.kernel.proofs import (  # noqa: E402
    AndElimL,
    AndElimR,
    AndIntro,
    Axiom,
    BotElim,
    CongAdd,
    CongMul,
    CongS,
    Cut,
    DNE,
    EqRefl,
    EqSubst,
    EqSym,
    EqTrans,
    ExistsElim,
    ExistsIntro,
    ForallElim,
    ForallIntro,
    Hyp,
    ImpElim,
    ImpIntro,
    Ind,
    OrElim,
    OrIntroL,
    OrIntroR,
)  # noqa: E402
from peano_lab.kernel.terms import Succ, Var, Zero  # noqa: E402
import training.peano_hydra.library_pilot_dependency_vector_cut_liveness as producer  # noqa: E402
import training.peano_hydra.library_pilot_dependency_vector_cut_liveness_verifier as verifier  # noqa: E402


SCHEMA_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library-pilot-dependency-vector-cut-liveness-schema-v1.json"
)
PRODUCER_PATH = (
    ROOT
    / "training/peano_hydra/library_pilot_dependency_vector_cut_liveness.py"
)
VERIFIER_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_dependency_vector_cut_liveness_verifier.py"
)
CLI_PATH = (
    ROOT
    / "scripts/build_peano_hydra_library_pilot_dependency_vector_cut_liveness.py"
)
VERIFY_CLI_PATH = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_dependency_vector_cut_liveness.py"
)

EXPECTED_INPUT = (
    "mul_add",
    "add_succ_left",
    "add_assoc",
    "add_comm",
)
EXPECTED_DERIVED = ("mul_add", "add_comm")
EXPECTED_ARTIFACT_SHA256 = (
    "c606af87e62b2e4d94303a0c8313efa9033d91c26321f7392351f471927ddc22"
)
EXPECTED_PROOF_SHA256 = (
    "5c480eb51b7bd0f1f0f8b3485cc071dc1f78aea2baace449533cad27d6dcf6b4"
)

PRODUCER_ERROR = producer.LibraryPilotDependencyVectorCutLivenessError
VERIFIER_ERROR = verifier.DependencyVectorCutLivenessVerificationError


def _tagged(proof: object) -> object:
    return json.loads(encode_proof(proof).decode("utf-8"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _reroot_candidate(value: dict[str, object]) -> dict[str, object]:
    result = deepcopy(value)
    theorem = result.get("theorem")
    if type(theorem) is dict:
        theorem["record_sha256"] = _sha256_json(
            {
                key: item
                for key, item in theorem.items()
                if key != "record_sha256"
            }
        )
        result["theorem_record_root_sha256"] = theorem["record_sha256"]
    body = {
        key: deepcopy(item)
        for key, item in result.items()
        if key not in ("root_preimage", "root_sha256")
    }
    preimage = {
        "format": producer.CUT_LIVENESS_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    result["root_preimage"] = preimage
    result["root_sha256"] = _sha256_json(preimage)
    return result


def _lf_receipt(names: tuple[str, ...]) -> dict[str, object]:
    raw = ("\n".join(names) + ("\n" if names else "")).encode("utf-8")
    return {
        "count": len(names),
        "dependencies": list(names),
        "lf_bytes": len(raw),
        "lf_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _load_cli():
    specification = importlib.util.spec_from_file_location(
        "_test_peano_hydra_a23d_cut_liveness_cli", CLI_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _load_verifier_cli():
    specification = importlib.util.spec_from_file_location(
        "_test_peano_hydra_a23d_cut_liveness_verifier_cli", VERIFY_CLI_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def controlled_python() -> Path:
    """Return the exact CPython minor version frozen by the runtime contract."""

    if sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 12):
        executable = Path(sys.executable)
    else:
        discovered = shutil.which("python3.12")
        if discovered is None:
            pytest.fail("the frozen controlled runtime requires CPython 3.12")
        executable = Path(discovered)
    version = subprocess.run(
        [str(executable), "--version"],
        check=False,
        capture_output=True,
        timeout=5,
    )
    assert version.returncode == 0
    assert (version.stdout + version.stderr).startswith(b"Python 3.12.")
    return executable


def _run_cli(
    controlled_python: Path,
    *arguments: str,
    timeout: float = 40,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(controlled_python), str(CLI_PATH), *arguments],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _run_verifier_cli(
    controlled_python: Path,
    *arguments: str,
    cwd: Path = ROOT,
    timeout: float = 40,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(controlled_python), str(VERIFY_CLI_PATH), *arguments],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _run_bounded_fixture(
    cli: object, command: list[str]
) -> subprocess.CompletedProcess[bytes]:
    read_descriptor, write_descriptor = os.pipe()
    token = b"bounded-child-fixture" * 4
    try:
        os.write(write_descriptor, token)
    finally:
        os.close(write_descriptor)
    try:
        environment = cli._controlled_environment(
            capability_fd=read_descriptor,
            capability_sha256=hashlib.sha256(token).hexdigest(),
        )
        return cli._run_bounded_child(command, environment=environment)
    finally:
        os.close(read_descriptor)


def _formula(level: int = 0) -> Eq:
    term = Zero()
    for _ in range(level):
        term = Succ(term)
    return Eq(term, term)


def _assert_object_and_tagged_liveness(proof: object, expected: int) -> None:
    assert producer._count_hypothesis_uses(proof) == expected
    assert verifier.derive_tagged_proof_liveness(
        _tagged(proof), outer_hypothesis_count=1
    ) == (expected,)


@pytest.fixture(scope="module")
def candidate() -> dict[str, object]:
    return producer.build_candidate_dependency_vector_cut_liveness(ROOT)


@pytest.fixture(scope="module")
def verification(candidate: dict[str, object]) -> dict[str, object]:
    return verifier.verify_dependency_vector_cut_liveness(candidate, ROOT)


def test_schema_registers_exact_scope_binders_limits_and_false_claims() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["algorithm"]["id"] == producer.ALGORITHM_ID
    assert schema["algorithm"]["scope"].startswith(
        "exact root direct-Cut spine only"
    )
    assert schema["algorithm"]["proposition_hypothesis_binders"] == [
        "ImpIntro.body",
        "Cut.body",
        "OrElim.left_case",
        "OrElim.right_case",
        "ExistsElim.body",
    ]
    assert (
        "intuitionistic-kernel-check every intermediate proof under the exact "
        "remaining surrounding dependency context"
        in schema["algorithm"]["normalization_contract"]
    )
    assert tuple(
        schema["fixed_inputs"]["root"]["declared_dependencies"]
    ) == EXPECTED_INPUT
    assert tuple(
        schema["canonical_output"]["derived_direct_dependencies"]
    ) == EXPECTED_DERIVED
    assert schema["canonical_output"]["artifact"] == {
        "artifact_bytes": 11_958,
        "artifact_sha256": EXPECTED_ARTIFACT_SHA256,
        "cut_nodes": 5,
        "fuel": 1_936,
        "fuel_formula": "8 * intrinsic_proof_nodes + 16",
        "proof_depth": 30,
        "proof_nodes": 240,
        "proof_term_sha256": EXPECTED_PROOF_SHA256,
    }
    assert schema["limits"] == {
        "max_artifact_bytes": 65_536,
        "max_cli_stderr_bytes": 65_536,
        "max_cli_stdout_bytes": 1_048_576,
        "max_cli_wall_seconds": 30,
        "max_dependency_count": 4,
        "max_document_bytes": 1_048_576,
        "max_formula_or_proof_depth": 128,
        "max_json_depth": 64,
        "max_json_nodes": 100_000,
        "max_proof_nodes": 10_000,
        "max_schema_bytes": 262_144,
        "max_transform_visits": 50_000,
    }
    false_claims = tuple(schema["claim_boundary"]["false_claims"])
    assert false_claims == producer._FALSE_CLAIMS
    assert false_claims == verifier.BROAD_FALSE_FIELDS

    runtime = schema["producer_contract"]["controlled_runtime"]
    assert runtime["python_implementation"] == "cpython"
    assert (runtime["python_major"], runtime["python_minor"]) == (3, 12)
    assert runtime["python_flags"] == ["-B", "-P", "-s", "-S"]
    assert runtime["python_hash_seed"] == "0"
    assert runtime["hash_randomization"] == 0
    assert runtime["python_optimize"] == 0
    assert runtime["producer_load_mode"] == (
        "authenticated-source-bytes-SourceFileLoader.source_to_code-exec"
    )
    closure = runtime["implementation_source_closure"]
    assert len(closure) == 8
    for row in closure:
        raw = (ROOT / row["path"]).read_bytes()
        assert len(raw) == row["bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]


def test_producer_and_verifier_have_no_predecessor_or_cross_imports() -> None:
    forbidden = {
        "training.peano_hydra.library_dependency_audit",
        "training.peano_hydra.library_construction_rebuild",
        "training.peano_hydra.library_optimizer_comparison_pilot",
        "training.peano_hydra.library_pilot_dependency_vector_audit",
        "training.peano_hydra.library_pilot_dependency_vector_negative_replay",
    }

    def imports(path: Path) -> set[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        result: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                result.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                result.add(node.module)
        return result

    producer_imports = imports(PRODUCER_PATH)
    verifier_imports = imports(VERIFIER_PATH)
    cli_imports = imports(CLI_PATH)
    verifier_cli_imports = imports(VERIFY_CLI_PATH)
    assert forbidden.isdisjoint(producer_imports)
    assert forbidden.isdisjoint(verifier_imports)
    assert forbidden.isdisjoint(cli_imports)
    assert forbidden.isdisjoint(verifier_cli_imports)
    producer_module = (
        "training.peano_hydra.library_pilot_dependency_vector_cut_liveness"
    )
    assert producer_module not in verifier_imports
    assert producer_module not in verifier_cli_imports
    for path in (PRODUCER_PATH, VERIFIER_PATH, CLI_PATH, VERIFY_CLI_PATH):
        source = path.read_text(encoding="utf-8")
        assert all(name not in source for name in forbidden)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert set(
        schema["producer_contract"]["predecessor_imports_forbidden"]
    ) == forbidden
    assert (
        "training.peano_hydra.library_pilot_dependency_vector_cut_liveness"
        not in verifier_imports
    )
    assert "peano_lab.engine.tactics" not in producer_imports | verifier_imports
    assert "peano_lab.library.theorems" not in producer_imports | verifier_imports


@pytest.mark.parametrize(
    ("proof", "expected"),
    (
        (ImpElim(Hyp(0), EqRefl(Zero())), 1),
        (AndIntro(Hyp(0), Hyp(0)), 2),
        (AndElimL(Hyp(0)), 1),
        (AndElimR(Hyp(0)), 1),
        (OrIntroL(Hyp(0)), 1),
        (OrIntroR(Hyp(0)), 1),
        (BotElim(Hyp(0)), 1),
        # A term binder does not change proposition-hypothesis indices.
        (ForallIntro(Hyp(0)), 1),
        (ForallElim(Hyp(0), Zero()), 1),
        (ExistsIntro(Zero(), Hyp(0)), 1),
        (EqSym(Hyp(0)), 1),
        (EqTrans(Hyp(0), Hyp(0)), 2),
        (CongS(Hyp(0)), 1),
        (CongAdd(Hyp(0), Hyp(0)), 2),
        (CongMul(Hyp(0), Hyp(0)), 2),
        (EqSubst(_formula(), Hyp(0), Hyp(0)), 2),
        (Ind(_formula(), Hyp(0), Hyp(0)), 2),
        (EqRefl(Zero()), 0),
        (Axiom("PA3"), 0),
    ),
)
def test_non_proposition_binders_and_leaf_constructors_agree(
    proof: object, expected: int
) -> None:
    _assert_object_and_tagged_liveness(proof, expected)


@pytest.mark.parametrize(
    ("proof", "expected"),
    (
        (ImpIntro(Hyp(0)), 0),
        (ImpIntro(Hyp(1)), 1),
        # Cut.lemma is in the surrounding context; Cut.body has one new slot.
        (Cut(_formula(), _formula(1), Hyp(0), Hyp(0)), 1),
        (Cut(_formula(), _formula(1), EqRefl(Zero()), Hyp(0)), 0),
        (Cut(_formula(), _formula(1), Hyp(0), Hyp(1)), 2),
        # Or branches each introduce one proposition hypothesis.
        (OrElim(Hyp(0), Hyp(0), Hyp(0)), 1),
        (OrElim(Hyp(0), Hyp(1), Hyp(1)), 3),
        # ExistsElim.body introduces both a term binder and one proposition
        # hypothesis, but only the latter changes Hyp indices.
        (ExistsElim(Hyp(0), Hyp(0)), 1),
        (ExistsElim(Hyp(0), Hyp(1)), 2),
    ),
)
def test_every_proposition_binder_has_exact_cutoff_semantics(
    proof: object, expected: int
) -> None:
    _assert_object_and_tagged_liveness(proof, expected)


def test_object_walker_is_inert_but_encoded_intuitionistic_verifier_rejects_dne() -> None:
    proof = DNE(_formula())
    assert producer._count_hypothesis_uses(proof) == 0
    with pytest.raises(VERIFIER_ERROR, match="DNE"):
        verifier.derive_tagged_proof_liveness(
            _tagged(proof), outer_hypothesis_count=1
        )


def test_drop_reindexes_only_free_outer_slots_under_every_binder() -> None:
    proposition = _formula()
    target = _formula(1)
    proof = AndIntro(
        ImpIntro(Hyp(2)),
        AndIntro(
            Cut(proposition, target, Hyp(1), Hyp(2)),
            OrElim(Hyp(1), Hyp(2), ExistsElim(Hyp(2), Hyp(3))),
        ),
    )
    assert producer._count_hypothesis_uses(proof) == 0
    lowered = producer._drop_vacuous_hypothesis(proof)
    expected = AndIntro(
        ImpIntro(Hyp(1)),
        AndIntro(
            Cut(proposition, target, Hyp(0), Hyp(1)),
            OrElim(Hyp(0), Hyp(1), ExistsElim(Hyp(1), Hyp(2))),
        ),
    )
    assert lowered == expected
    encoded = _tagged(proof)
    assert verifier.derive_tagged_proof_liveness(
        encoded, outer_hypothesis_count=2
    ) == (0, 7)
    assert verifier.thin_tagged_proof_outer_context(
        encoded, outer_hypothesis_count=2, live_slots=(1,)
    ) == _tagged(expected)


def test_drop_refuses_live_slot_malformed_cutoffs_and_unsupported_proofs() -> None:
    for cutoff in (-1, True, 1.5):
        with pytest.raises(PRODUCER_ERROR, match="cutoff|non-negative"):
            producer._count_hypothesis_uses(Hyp(0), cutoff)  # type: ignore[arg-type]
    with pytest.raises(PRODUCER_ERROR, match="used"):
        producer._drop_vacuous_hypothesis(Hyp(0))

    class ForeignHyp(Hyp):
        pass

    with pytest.raises(PRODUCER_ERROR, match="exact kernel proof|unsupported"):
        producer._count_hypothesis_uses(ForeignHyp(0))


def test_encoded_transform_rejects_bad_context_maps_and_dne() -> None:
    with pytest.raises(VERIFIER_ERROR, match="outside its context"):
        verifier.derive_tagged_proof_liveness(
            ["hyp", 1], outer_hypothesis_count=1
        )
    for live_slots in ((1,), (0, 0), (1, 0), (True,)):
        with pytest.raises(VERIFIER_ERROR, match="thinning map"):
            verifier.thin_tagged_proof_outer_context(
                ["hyp", 0], outer_hypothesis_count=1, live_slots=live_slots
            )
    with pytest.raises(VERIFIER_ERROR, match="delete a live"):
        verifier.thin_tagged_proof_outer_context(
            ["hyp", 0], outer_hypothesis_count=1, live_slots=()
        )
    with pytest.raises(VERIFIER_ERROR, match="DNE"):
        verifier.derive_tagged_proof_liveness(
            ["dne", ["eq", ["zero"], ["zero"]]],
            outer_hypothesis_count=0,
        )


def _two_dependency_spine(terminal: object):
    first = _formula()
    second = _formula(1)
    target = _formula(2)
    first_lemma = EqRefl(Zero())
    second_lemma = EqRefl(Succ(Zero()))
    proof = Cut(
        first,
        target,
        first_lemma,
        Cut(second, target, second_lemma, terminal),
    )
    dependencies = (
        ("first", first, first_lemma),
        ("second", second, second_lemma),
    )
    return proof, target, dependencies


@pytest.mark.parametrize(
    ("terminal", "target", "expected"),
    (
        (Hyp(1), _formula(), ("first",)),
        (Hyp(0), _formula(1), ("second",)),
        (EqRefl(Succ(Succ(Zero()))), _formula(2), ()),
    ),
)
def test_inner_first_normalization_derives_live_spine_subsequence(
    terminal: object, target: object, expected: tuple[str, ...]
) -> None:
    proof, _unused_target, dependencies = _two_dependency_spine(terminal)
    # The helper target must match the terminal fixture for the proof to check.
    first, second = dependencies
    proof = Cut(
        first[1],
        target,
        first[2],
        Cut(second[1], target, second[2], terminal),
    )
    assert check((), proof, target)
    normalized = producer._normalize_direct_spine(
        proof, target, dependencies
    )
    assert normalized.retained_dependencies == expected
    assert check((), normalized.proof, target)
    second_pass_dependencies = tuple(
        entry for entry in dependencies if entry[0] in expected
    )
    if second_pass_dependencies:
        second_pass = producer._normalize_direct_spine(
            normalized.proof, target, second_pass_dependencies
        )
        assert second_pass.proof == normalized.proof
        assert second_pass.retained_dependencies == expected


def test_internal_cut_lemma_is_reindexed_but_direct_lemma_stays_opaque() -> None:
    first = _formula()
    second = _formula(1)
    first_lemma = EqRefl(Zero())
    second_lemma = EqRefl(Succ(Zero()))
    tail = _formula(2)
    target = And(first, tail)
    terminal = AndIntro(Cut(first, first, Hyp(1), Hyp(0)), EqRefl(Succ(Succ(Zero()))))
    proof = Cut(
        first,
        target,
        first_lemma,
        Cut(second, target, second_lemma, terminal),
    )
    dependencies = (
        ("first", first, first_lemma),
        ("second", second, second_lemma),
    )
    assert check((), proof, target)
    normalized = producer._normalize_direct_spine(proof, target, dependencies)
    assert normalized.retained_dependencies == ("first",)
    assert type(normalized.proof) is Cut
    assert normalized.proof.lemma is first_lemma
    assert encode_proof(normalized.proof.lemma) == encode_proof(first_lemma)
    assert type(normalized.proof.body) is AndIntro
    assert type(normalized.proof.body.left) is Cut
    assert normalized.proof.body.left.lemma == Hyp(0)
    assert check((), normalized.proof, target)


def test_normalization_rejects_wrong_spine_mapping_and_extra_root_cut() -> None:
    proof, target, dependencies = _two_dependency_spine(
        EqRefl(Succ(Succ(Zero())))
    )
    wrong = (
        (dependencies[0][0], dependencies[1][1], dependencies[1][2]),
        dependencies[1],
    )
    with pytest.raises(PRODUCER_ERROR, match="carrier differs"):
        producer._normalize_direct_spine(proof, target, wrong)
    extra = Cut(_formula(3), target, EqRefl(Succ(Succ(Succ(Zero())))), proof)
    with pytest.raises(PRODUCER_ERROR, match="carrier differs|unexpected"):
        producer._normalize_direct_spine(extra, target, dependencies)


def test_transform_visit_caps_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(producer, "MAX_TRANSFORM_VISITS", 1)
    with pytest.raises(PRODUCER_ERROR, match="visit limit"):
        producer._count_hypothesis_uses(ImpIntro(Hyp(0)))
    with pytest.raises(VERIFIER_ERROR, match="bound"):
        verifier.derive_tagged_proof_liveness(
            ["imp_intro", ["hyp", 0]],
            outer_hypothesis_count=0,
            max_visits=1,
        )


def test_canonical_encoders_reject_non_json_and_output_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(PRODUCER_ERROR, match="unsupported JSON"):
        producer.canonical_document_bytes({"bad": 1.5})
    cycle: list[object] = []
    cycle.append(cycle)
    with pytest.raises(PRODUCER_ERROR, match="structural limit"):
        producer.canonical_document_bytes(cycle)
    monkeypatch.setattr(producer, "MAX_DOCUMENT_BYTES", 8)
    with pytest.raises(PRODUCER_ERROR, match="byte limit"):
        producer.canonical_document_bytes({"value": "too large"})
    monkeypatch.setattr(verifier, "MAX_DOCUMENT_BYTES", 8)
    monkeypatch.setattr(
        verifier,
        "validate_dependency_vector_cut_liveness_verification",
        lambda value: value,
    )
    with pytest.raises(VERIFIER_ERROR, match="byte limit"):
        verifier.canonical_verification_bytes({"value": "too large"})


@pytest.mark.parametrize("kind", ("directory", "symlink", "fifo", "oversize"))
def test_candidate_loader_rejects_nonregular_links_fifos_and_oversize(
    tmp_path: Path, kind: str
) -> None:
    path = tmp_path / "candidate.json"
    if kind == "directory":
        path.mkdir()
    elif kind == "symlink":
        target = tmp_path / "target.json"
        target.write_text("{}\n", encoding="utf-8")
        path.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.write_bytes(b"x" * (producer.MAX_DOCUMENT_BYTES + 1))
    with pytest.raises(PRODUCER_ERROR, match="regular|bounded|bound"):
        producer.load_dependency_vector_cut_liveness(path, ROOT)


@pytest.mark.parametrize("kind", ("directory", "symlink", "fifo", "oversize"))
def test_verification_loader_rejects_nonregular_links_fifos_and_oversize(
    tmp_path: Path, kind: str
) -> None:
    path = tmp_path / "verification.json"
    if kind == "directory":
        path.mkdir()
    elif kind == "symlink":
        target = tmp_path / "target.json"
        target.write_text("{}\n", encoding="utf-8")
        path.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.write_bytes(b"x" * (verifier.MAX_DOCUMENT_BYTES + 1))
    with pytest.raises(VERIFIER_ERROR, match="regular|bounded|bound"):
        verifier.load_dependency_vector_cut_liveness_verification(path)


def test_create_only_is_exact_and_never_overwrites(tmp_path: Path) -> None:
    cli = _load_cli()
    path = tmp_path / "candidate.json"
    raw = b'{"candidate":true}\n'
    cli._create_only(path, raw)
    assert path.read_bytes() == raw
    assert stat.S_IMODE(path.stat().st_mode) & 0o600 == 0o600
    with pytest.raises(cli.CutLivenessCLIError, match="already exists"):
        cli._create_only(path, b"replacement\n")
    assert path.read_bytes() == raw


def test_create_only_rejects_symlink_ancestor_and_output_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(cli.CutLivenessCLIError, match="symlink"):
        cli._create_only(linked / "candidate.json", b"{}\n")
    monkeypatch.setattr(cli, "MAX_DOCUMENT_BYTES", 8)
    with pytest.raises(cli.CutLivenessCLIError, match="byte limit"):
        cli._canonical_bytes({"value": "too large"})


def test_create_only_rejects_same_byte_path_substitution_without_unlinking_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    path = tmp_path / "candidate.json"
    displaced = tmp_path / "displaced-created-inode.json"
    raw = b'{"candidate":true}\n'
    original_fsync = cli.os.fsync

    def swap_after_sync(descriptor: int) -> None:
        original_fsync(descriptor)
        path.rename(displaced)
        path.write_bytes(raw)

    monkeypatch.setattr(cli.os, "fsync", swap_after_sync)
    with pytest.raises(cli.CutLivenessCLIError, match="identity"):
        cli._create_only(path, raw)
    assert displaced.read_bytes() == raw
    assert path.read_bytes() == raw
    assert path.stat().st_ino != displaced.stat().st_ino


def test_cli_authenticates_exact_sources_and_executes_only_captured_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    schema_raw, producer_raw, captured = cli._authenticate_sources()
    assert len(schema_raw) == cli.SCHEMA_SOURCE_BYTES
    assert hashlib.sha256(schema_raw).hexdigest() == cli.SCHEMA_SOURCE_SHA256
    assert len(producer_raw) == cli.PRODUCER_SOURCE_BYTES
    assert hashlib.sha256(producer_raw).hexdigest() == cli.PRODUCER_SOURCE_SHA256
    assert set(captured) == {row[0] for row in cli._CAPTURED_SOURCE_ROWS}
    for name, path, expected_bytes, expected_sha, is_package in (
        cli._CAPTURED_SOURCE_ROWS
    ):
        captured_path, raw, captured_is_package = captured[name]
        assert captured_path == ROOT / path
        assert captured_is_package is is_package
        assert len(raw) == expected_bytes
        assert hashlib.sha256(raw).hexdigest() == expected_sha

    fixture_path = tmp_path / "captured_fixture.py"
    fixture_path.write_bytes(b"VALUE = 'substituted-path-bytes'\n")
    module_name = "_a23d_captured_source_fixture"
    monkeypatch.setattr(sys, "pycache_prefix", cli.PYCACHE_PREFIX)
    try:
        module = cli._execute_captured_module(
            module_name,
            fixture_path,
            b"VALUE = 'authenticated-captured-bytes'\n",
            is_package=False,
        )
        assert module.VALUE == "authenticated-captured-bytes"
    finally:
        sys.modules.pop(module_name, None)


def test_cli_controlled_environment_removes_python_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    monkeypatch.setenv("PYTHONPATH", "/attacker")
    monkeypatch.setenv("PYTHONINSPECT", "1")
    monkeypatch.setenv("VIRTUAL_ENV", "/attacker/venv")
    environment = cli._controlled_environment(
        capability_fd=17,
        capability_sha256="0" * 64,
    )
    python_environment = {
        name: value
        for name, value in environment.items()
        if name.startswith("PYTHON")
    }
    assert python_environment == {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONPYCACHEPREFIX": cli.PYCACHE_PREFIX,
    }
    assert environment[cli._WORKER_ENVIRONMENT] == "1"
    assert environment[cli._WORKER_PARENT_RUNTIME] == cli.PYTHON_RUNTIME_TAG
    assert environment[cli._WORKER_CAPABILITY_FD] == "17"
    assert environment[cli._WORKER_CAPABILITY_SHA256] == "0" * 64
    assert "VIRTUAL_ENV" not in environment


@pytest.mark.parametrize("stream", ("stdout", "stderr"))
def test_cli_bounded_child_enforces_each_output_cap(
    controlled_python: Path,
    monkeypatch: pytest.MonkeyPatch,
    stream: str,
) -> None:
    cli = _load_cli()
    if stream == "stdout":
        monkeypatch.setattr(cli, "MAX_STDOUT_BYTES", 32)
        program = "import sys;sys.stdout.buffer.write(b'x'*33)"
    else:
        monkeypatch.setattr(cli, "MAX_STDERR_BYTES", 32)
        program = "import sys;sys.stderr.buffer.write(b'x'*33)"
    with pytest.raises(cli.CutLivenessCLIError, match=f"{stream}.*hard byte cap"):
        _run_bounded_fixture(
            cli,
            [
                str(controlled_python),
                "-B",
                "-P",
                "-s",
                "-S",
                "-c",
                program,
            ],
        )


def test_cli_bounded_child_enforces_wall_time(
    controlled_python: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    monkeypatch.setattr(cli, "MAX_WALL_SECONDS", 0.05)
    with pytest.raises(cli.CutLivenessCLIError, match="wall-time cap"):
        _run_bounded_fixture(
            cli,
            [
                str(controlled_python),
                "-B",
                "-P",
                "-s",
                "-S",
                "-c",
                "import time;time.sleep(2)",
            ],
        )


def test_cli_default_protocol_and_direct_worker_runtime_boundary(
    controlled_python: Path,
) -> None:
    described = _run_cli(controlled_python)
    assert described.returncode == 0
    assert described.stderr == b""
    receipt = json.loads(described.stdout)
    assert receipt["status"] == "described-no-build-no-write"
    assert receipt["build_executed"] is False
    assert receipt["candidate_artifact_created"] is False
    assert receipt["default_write"] is False
    assert receipt["runtime"] == {
        "bounded_child": True,
        "hash_randomization": 0,
        "max_stderr_bytes": 65_536,
        "max_stdout_bytes": 1_048_576,
        "max_wall_seconds": 30,
        "producer_load_mode": (
            "authenticated-source-bytes-SourceFileLoader.source_to_code-exec"
        ),
        "pycache_prefix": (
            "/proc/peano-hydra-a23d-cut-liveness-disabled-pycache"
        ),
        "python_flags": ["-B", "-P", "-s", "-S"],
        "python_hash_seed": "0",
        "python_implementation": "cpython",
        "python_major": 3,
        "python_minor": 12,
        "python_optimize": 0,
    }

    direct_worker = _run_cli(
        controlled_python, "--_controlled-worker", "--describe"
    )
    assert direct_worker.returncode == 2
    assert direct_worker.stdout == b""
    assert b"worker requires fresh controlled Python" in direct_worker.stderr
    assert len(direct_worker.stderr) <= 65_536


def test_cli_build_validate_create_only_and_no_overwrite(
    tmp_path: Path,
    controlled_python: Path,
    candidate: dict[str, object],
) -> None:
    expected = producer.canonical_document_bytes(candidate)
    built = _run_cli(controlled_python, "--build")
    assert built.returncode == 0
    assert built.stderr == b""
    assert built.stdout == expected

    candidate_path = tmp_path / "candidate-input.json"
    candidate_path.write_bytes(expected)
    validated = _run_cli(
        controlled_python, "--validate", str(candidate_path)
    )
    assert validated.returncode == 0
    assert validated.stderr == b""
    assert validated.stdout == expected

    output_path = tmp_path / "created-candidate.json"
    wrong_confirmation = _run_cli(
        controlled_python,
        "--build",
        "--output",
        str(output_path),
        "--confirm-create",
        "wrong-token",
    )
    assert wrong_confirmation.returncode == 2
    assert wrong_confirmation.stdout == b""
    assert b"exact --confirm-create token" in wrong_confirmation.stderr
    assert not output_path.exists()

    cli = _load_cli()
    created = _run_cli(
        controlled_python,
        "--build",
        "--output",
        str(output_path),
        "--confirm-create",
        cli.CONFIRMATION,
    )
    assert created.returncode == 0
    assert created.stdout == b""
    assert created.stderr == b""
    assert output_path.read_bytes() == expected

    overwritten = _run_cli(
        controlled_python,
        "--build",
        "--output",
        str(output_path),
        "--confirm-create",
        cli.CONFIRMATION,
    )
    assert overwritten.returncode == 2
    assert overwritten.stdout == b""
    assert b"already exists" in overwritten.stderr
    assert output_path.read_bytes() == expected


@pytest.mark.parametrize("kind", ("directory", "symlink", "fifo", "oversize"))
def test_cli_validate_rejects_nonregular_or_oversize_input(
    tmp_path: Path,
    controlled_python: Path,
    kind: str,
) -> None:
    path = tmp_path / "candidate.json"
    if kind == "directory":
        path.mkdir()
    elif kind == "symlink":
        target = tmp_path / "target.json"
        target.write_text("{}\n", encoding="utf-8")
        path.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.write_bytes(b"x" * (producer.MAX_DOCUMENT_BYTES + 1))
    rejected = _run_cli(controlled_python, "--validate", str(path))
    assert rejected.returncode == 2
    assert rejected.stdout == b""
    assert any(
        fragment in rejected.stderr
        for fragment in (b"regular", b"bound", b"byte limit")
    )
    assert len(rejected.stderr) <= 65_536


def test_cli_rejects_repository_root_aliases_and_other_trees(
    tmp_path: Path, controlled_python: Path
) -> None:
    alias = tmp_path / "root-alias"
    alias.symlink_to(ROOT, target_is_directory=True)
    for repository_root in (tmp_path, alias):
        rejected = _run_cli(
            controlled_python,
            "--repository-root",
            str(repository_root),
        )
        assert rejected.returncode == 2
        assert rejected.stdout == b""
        assert (
            b"repository root" in rejected.stderr
            or b"repository-root" in rejected.stderr
        )


def test_verifier_cli_default_runtime_and_direct_worker_boundary(
    controlled_python: Path,
) -> None:
    described = _run_verifier_cli(controlled_python)
    assert described.returncode == 0
    assert described.stderr == b""
    receipt = json.loads(described.stdout)
    assert receipt["status"] == "described-no-verification-no-write"
    assert receipt["independent_verification_executed"] is False
    assert receipt["producer_imported"] is False
    assert receipt["default_write"] is False
    assert receipt["runtime"] == {
        "bounded_child": True,
        "hash_randomization": 0,
        "max_stderr_bytes": 65_536,
        "max_stdout_bytes": 1_048_576,
        "max_wall_seconds": 30,
        "pycache_prefix": "/proc/peano-hydra-a23d-verifier-disabled-pycache",
        "python_flags": ["-B", "-P", "-s", "-S"],
        "python_hash_seed": "0",
        "python_implementation": "cpython",
        "python_major": 3,
        "python_minor": 12,
        "python_optimize": 0,
        "verifier_load_mode": (
            "authenticated-source-bytes-SourceFileLoader.source_to_code-exec"
        ),
    }
    verifier_source = receipt["verifier_source"]
    raw = VERIFIER_PATH.read_bytes()
    assert verifier_source["artifact_bytes"] == len(raw)
    assert verifier_source["artifact_sha256"] == hashlib.sha256(raw).hexdigest()

    direct_worker = _run_verifier_cli(
        controlled_python, "--_controlled-worker", "--describe"
    )
    assert direct_worker.returncode == 2
    assert direct_worker.stdout == b""
    assert b"requires exact fresh -B -P -s -S" in direct_worker.stderr
    assert len(direct_worker.stderr) <= 65_536


def test_verifier_cli_preserves_relative_paths_across_controlled_worker_cwd(
    tmp_path: Path,
    controlled_python: Path,
    candidate: dict[str, object],
    verification: dict[str, object],
) -> None:
    candidate_path = tmp_path / "relative-candidate.json"
    candidate_path.write_bytes(producer.canonical_document_bytes(candidate))
    relative_root = os.path.relpath(ROOT, start=tmp_path)
    completed = _run_verifier_cli(
        controlled_python,
        "--verify",
        candidate_path.name,
        "--repository-root",
        relative_root,
        cwd=tmp_path,
    )
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout == verifier.canonical_verification_bytes(verification)


def test_verifier_cli_create_only_confirmation_and_no_overwrite(
    tmp_path: Path,
    controlled_python: Path,
    candidate: dict[str, object],
    verification: dict[str, object],
) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_bytes(producer.canonical_document_bytes(candidate))
    output_path = tmp_path / "verification.json"
    expected = verifier.canonical_verification_bytes(verification)
    cli = _load_verifier_cli()

    wrong = _run_verifier_cli(
        controlled_python,
        "--verify",
        str(candidate_path),
        "--output",
        str(output_path),
        "--confirm-create",
        "wrong-token",
    )
    assert wrong.returncode == 2
    assert wrong.stdout == b""
    assert b"exact --confirm-create token" in wrong.stderr
    assert not output_path.exists()

    created = _run_verifier_cli(
        controlled_python,
        "--verify",
        str(candidate_path),
        "--output",
        str(output_path),
        "--confirm-create",
        cli.CONFIRMATION,
    )
    assert created.returncode == 0
    assert created.stdout == b""
    assert created.stderr == b""
    assert output_path.read_bytes() == expected

    overwrite = _run_verifier_cli(
        controlled_python,
        "--verify",
        str(candidate_path),
        "--output",
        str(output_path),
        "--confirm-create",
        cli.CONFIRMATION,
    )
    assert overwrite.returncode == 2
    assert overwrite.stdout == b""
    assert b"already exists" in overwrite.stderr
    assert output_path.read_bytes() == expected


def test_verifier_cli_publish_rejects_same_byte_inode_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_verifier_cli()
    path = tmp_path / "verification.json"
    displaced = tmp_path / "displaced-created-inode.json"
    raw = b'{"verification":true}\n'
    original_fsync = cli.os.fsync

    def swap_after_sync(descriptor: int) -> None:
        original_fsync(descriptor)
        path.rename(displaced)
        path.write_bytes(raw)

    monkeypatch.setattr(cli.os, "fsync", swap_after_sync)
    with pytest.raises(cli.DependencyVectorCutLivenessVerifierCLIError, match="identity"):
        cli._publish_create_only(path, raw)
    assert displaced.read_bytes() == raw
    assert path.read_bytes() == raw
    assert path.stat().st_ino != displaced.stat().st_ino


@pytest.mark.parametrize("stream", ("stdout", "stderr"))
def test_verifier_cli_controlled_child_enforces_output_caps(
    tmp_path: Path,
    controlled_python: Path,
    monkeypatch: pytest.MonkeyPatch,
    stream: str,
) -> None:
    cli = _load_verifier_cli()

    class ControlledRuntime:
        executable = str(controlled_python)

    monkeypatch.setattr(cli, "sys", ControlledRuntime)
    if stream == "stdout":
        monkeypatch.setattr(cli, "MAX_STDOUT_BYTES", 32)
        arguments = ["--describe"]
    else:
        monkeypatch.setattr(cli, "MAX_STDERR_BYTES", 32)
        arguments = ["--verify", str(tmp_path / "absent.json")]
    with pytest.raises(
        cli.DependencyVectorCutLivenessVerifierCLIError,
        match="output bound",
    ):
        cli._run_bounded_worker(arguments)


def test_verifier_cli_controlled_child_enforces_wall_time(
    controlled_python: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_verifier_cli()

    class ControlledRuntime:
        executable = str(controlled_python)

    monkeypatch.setattr(cli, "sys", ControlledRuntime)
    monkeypatch.setattr(cli, "MAX_WALL_SECONDS", -1)
    with pytest.raises(
        cli.DependencyVectorCutLivenessVerifierCLIError,
        match="wall-time bound",
    ):
        cli._run_bounded_worker(["--describe"])


def test_cli_rejects_an_unsupported_parent_runtime_cleanly() -> None:
    if sys.implementation.name == "cpython" and sys.version_info[:2] != (3, 12):
        for path, marker in (
            (CLI_PATH, b"controlled parent requires CPython 3.12 exactly"),
            (
                VERIFY_CLI_PATH,
                b"controlled verifier parent requires CPython 3.12 exactly",
            ),
        ):
            rejected = subprocess.run(
                [sys.executable, str(path)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=5,
            )
            assert rejected.returncode == 2
            assert rejected.stdout == b""
            assert marker in rejected.stderr
            assert b"Unknown option" not in rejected.stderr
            assert len(rejected.stderr) <= 65_536
    else:
        for cli, error in (
            (_load_cli(), "CutLivenessCLIError"),
            (
                _load_verifier_cli(),
                "DependencyVectorCutLivenessVerifierCLIError",
            ),
        ):
            with pytest.raises(
                getattr(cli, error), match="CPython 3.12 exactly"
            ):
                original = cli.PYTHON_VERSION
                try:
                    cli.PYTHON_VERSION = (99, 99)
                    cli._require_runtime_version(role="parent")
                finally:
                    cli.PYTHON_VERSION = original


def test_exact_candidate_binds_input_transform_artifact_and_narrow_claims(
    candidate: dict[str, object],
) -> None:
    assert candidate["format"] == producer.CUT_LIVENESS_FORMAT
    assert candidate["id"] == producer.CUT_LIVENESS_ID
    assert candidate["status"] == producer.STATUS
    assert candidate["logic_mode"] == "intuitionistic"
    assert candidate["aggregate"] == {
        "candidate_artifact_count": 1,
        "deleted_vacuous_root_cut_count": 2,
        "derived_direct_dependency_count": 2,
        "initial_direct_dependency_count": 4,
        "pilot_theorem_count": 1,
        "retained_used_root_cut_count": 2,
    }
    assert candidate["algorithm"] == {
        "id": producer.ALGORITHM_ID,
        "opaque_direct_lemmas_transformed": False,
        "processing_order": "inner-first",
        "proof_producing": True,
        "scope": "exact-declared-root-direct-cut-spine-only",
    }
    for field in producer._FALSE_CLAIMS:
        assert candidate[field] is False

    theorem = candidate["theorem"]
    assert type(theorem) is dict
    for field in producer._FALSE_CLAIMS:
        assert theorem[field] is False
    assert theorem["initial_direct_vector"] == _lf_receipt(EXPECTED_INPUT)
    assert theorem["derived_direct_vector"] == _lf_receipt(EXPECTED_DERIVED)
    assert [row["name"] for row in theorem["input_direct_cut_spine"]] == list(
        EXPECTED_INPUT
    )
    steps = theorem["normalization_steps_inner_first"]
    assert [
        (row["dependency"], row["bound_hypothesis_use_count"], row["outcome"])
        for row in steps
    ] == [
        ("add_comm", 2, "retained-used"),
        ("add_assoc", 0, "deleted-vacuous"),
        ("add_succ_left", 0, "deleted-vacuous"),
        ("mul_add", 1, "retained-used"),
    ]
    expected_step_fields = {
        "bound_hypothesis_use_count",
        "declared_index",
        "dependency",
        "first_use_path",
        "input_body_proof_sha256",
        "intermediate_kernel_checked",
        "opaque_lemma_proof_sha256",
        "outcome",
        "output_proof_sha256",
        "processing_index",
        "surrounding_context_nearest_first",
    }
    for processing_index, row in enumerate(steps):
        assert set(row) == expected_step_fields
        assert row["processing_index"] == processing_index
        assert row["declared_index"] == 3 - processing_index
        assert row["intermediate_kernel_checked"] is True
        assert (row["first_use_path"] is not None) == (
            row["bound_hypothesis_use_count"] > 0
        )
        if processing_index:
            assert row["input_body_proof_sha256"] == steps[processing_index - 1][
                "output_proof_sha256"
            ]
    assert steps[-1]["output_proof_sha256"] == EXPECTED_PROOF_SHA256
    artifact = theorem["candidate_artifact"]
    assert artifact["artifact_bytes"] == 11_958
    assert artifact["artifact_sha256"] == EXPECTED_ARTIFACT_SHA256
    assert artifact["proof_term_sha256"] == EXPECTED_PROOF_SHA256
    assert artifact["fuel"] == 1_936
    assert artifact["tree_metrics"] == {
        "cut_nodes": 5,
        "proof_depth": 30,
        "proof_nodes": 240,
    }
    raw = base64.b64decode(artifact["artifact_base64"], validate=True)
    assert len(raw) == 11_958
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_ARTIFACT_SHA256
    output_fuel, output_target, output_proof = decode_artifact(raw)
    assert output_fuel == 1_936
    assert check((), output_proof, output_target)
    assert hashlib.sha256(encode_proof(output_proof)).hexdigest() == (
        EXPECTED_PROOF_SHA256
    )

    replay_root = (
        ROOT / candidate["inputs"]["replay_manifest"]["artifact_path"]
    ).parent
    root_row = candidate["inputs"]["root_artifact"]
    input_raw = (replay_root / root_row["artifact_path"]).read_bytes()
    assert len(input_raw) == root_row["artifact_bytes"]
    assert hashlib.sha256(input_raw).hexdigest() == root_row["artifact_sha256"]
    input_fuel, input_target, input_proof = decode_artifact(input_raw)
    assert input_fuel == root_row["fuel"]
    assert input_target == output_target
    assert check((), input_proof, input_target)
    assert hashlib.sha256(encode_proof(input_proof)).hexdigest() == (
        root_row["proof_term_sha256"]
    )

    dependency_rows = {
        row["name"]: row for row in candidate["inputs"]["dependency_artifacts"]
    }
    assert tuple(dependency_rows) == EXPECTED_INPUT
    for name, row in dependency_rows.items():
        dependency_raw = (replay_root / row["artifact_path"]).read_bytes()
        assert len(dependency_raw) == row["artifact_bytes"]
        assert hashlib.sha256(dependency_raw).hexdigest() == row["artifact_sha256"]
        _fuel, dependency_target, dependency_proof = decode_artifact(
            dependency_raw
        )
        assert check((), dependency_proof, dependency_target)
        assert hashlib.sha256(encode_proof(dependency_proof)).hexdigest() == (
            row["proof_term_sha256"]
        )
        spine_row = next(
            item
            for item in theorem["input_direct_cut_spine"]
            if item["name"] == name
        )
        assert spine_row["artifact_sha256"] == row["artifact_sha256"]
        assert spine_row["opaque_lemma_proof_sha256"] == row["proof_term_sha256"]
        step_row = next(item for item in steps if item["dependency"] == name)
        assert step_row["opaque_lemma_proof_sha256"] == row["proof_term_sha256"]

    input_cursor = input_proof
    input_lemmas: dict[str, object] = {}
    for row in theorem["input_direct_cut_spine"]:
        assert isinstance(input_cursor, Cut)
        input_lemmas[row["name"]] = input_cursor.lemma
        assert hashlib.sha256(encode_proof(input_cursor.lemma)).hexdigest() == (
            row["opaque_lemma_proof_sha256"]
        )
        input_cursor = input_cursor.body
    output_cursor = output_proof
    for retained_name in EXPECTED_DERIVED:
        assert isinstance(output_cursor, Cut)
        input_row = next(
            row
            for row in theorem["input_direct_cut_spine"]
            if row["name"] == retained_name
        )
        assert encode_proof(output_cursor.lemma) == encode_proof(
            input_lemmas[retained_name]
        )
        assert hashlib.sha256(encode_proof(output_cursor.lemma)).hexdigest() == (
            input_row["opaque_lemma_proof_sha256"]
        )
        output_cursor = output_cursor.body
    assert theorem["closure_context"]["dropped_direct_dependencies_remaining_reachable"] == [
        "add_succ_left",
        "add_assoc",
    ]
    assert theorem["closure_context"]["unchanged"] is True
    survival = theorem["opaque_lemma_subtree_survival"]
    assert [
        (
            row["dependency"],
            row["direct_cut_retained"],
            row["input_subtree_occurrences"],
            row["output_subtree_occurrences"],
            row["survives_elsewhere_after_root_cut_deletion"],
        )
        for row in survival
    ] == [
        ("mul_add", True, 1, 1, False),
        ("add_succ_left", False, 2, 1, True),
        ("add_assoc", False, 2, 1, True),
        ("add_comm", True, 1, 1, False),
    ]
    assert producer.validate_dependency_vector_cut_liveness(candidate, ROOT) == candidate


def test_independent_verification_derives_bytes_and_keeps_broad_claims_false(
    candidate: dict[str, object], verification: dict[str, object]
) -> None:
    assert verification["status"] == "passed"
    assert verification["producer_imported_by_verifier"] is False
    for field in verifier.VERIFICATION_FALSE_FIELDS:
        assert verification[field] is False
    for field in (
        "derived_artifact_byte_identical",
        "derived_direct_vector_independently_reproduced",
        "encoded_tagged_array_transform_independently_executed",
        "input_and_dependency_artifacts_independently_authenticated",
        "input_and_output_kernel_checked",
        "proof_liveness_transform_idempotent",
    ):
        assert verification[field] is True
    theorem = verification["theorem"]
    assert theorem["input_direct_cut_spine"] == list(EXPECTED_INPUT)
    assert theorem["derived_direct_dependencies"] == list(EXPECTED_DERIVED)
    assert theorem["candidate_artifact_sha256"] == EXPECTED_ARTIFACT_SHA256
    assert theorem["output_proof_term_sha256"] == EXPECTED_PROOF_SHA256
    assert theorem["output_fuel"] == 1_936
    assert theorem["output_metrics"] == {
        "cut_nodes": 5,
        "proof_depth": 30,
        "proof_nodes": 240,
    }
    assert theorem["normalization_steps_inner_first"] == [
        {
            "dependency": "add_comm",
            "hypothesis_occurrences": 2,
            "outcome": "retained-used",
        },
        {
            "dependency": "add_assoc",
            "hypothesis_occurrences": 0,
            "outcome": "deleted-vacuous",
        },
        {
            "dependency": "add_succ_left",
            "hypothesis_occurrences": 0,
            "outcome": "deleted-vacuous",
        },
        {
            "dependency": "mul_add",
            "hypothesis_occurrences": 1,
            "outcome": "retained-used",
        },
    ]
    assert verifier.validate_dependency_vector_cut_liveness_verification(
        verification
    ) == verification
    assert verification["candidate_root_sha256"] == candidate["root_sha256"]


def test_encoded_verifier_is_independent_of_live_producer_helpers(
    candidate: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(producer, "_count_hypothesis_uses", lambda *_args: 99)
    monkeypatch.setattr(
        producer,
        "_drop_vacuous_hypothesis",
        lambda *_args: (_ for _ in ()).throw(AssertionError("producer called")),
    )
    receipt = verifier.verify_dependency_vector_cut_liveness(candidate, ROOT)
    assert receipt["derived_direct_vector_independently_reproduced"] is True
    assert receipt["producer_imported_by_verifier"] is False


@pytest.mark.parametrize(
    "mutation",
    ("vector", "step", "artifact", "unknown-top-level"),
)
def test_semantic_candidate_forgery_is_rejected_even_after_complete_reroot(
    candidate: dict[str, object], mutation: str
) -> None:
    forged = deepcopy(candidate)
    theorem = forged["theorem"]
    if mutation == "vector":
        theorem["derived_direct_vector"] = _lf_receipt(
            ("mul_add", "add_assoc", "add_comm")
        )
    elif mutation == "step":
        theorem["normalization_steps_inner_first"][1]["outcome"] = "retained-used"
        theorem["normalization_steps_inner_first"][1][
            "bound_hypothesis_use_count"
        ] = 1
    elif mutation == "artifact":
        artifact = theorem["candidate_artifact"]
        raw = bytearray(base64.b64decode(artifact["artifact_base64"], validate=True))
        raw[-2] ^= 1
        artifact["artifact_base64"] = base64.b64encode(raw).decode("ascii")
        artifact["artifact_sha256"] = hashlib.sha256(raw).hexdigest()
    else:
        forged["unreviewed_semantic_claim"] = True
    forged = _reroot_candidate(forged)
    with pytest.raises(PRODUCER_ERROR, match="differs from exact reconstruction"):
        producer.validate_dependency_vector_cut_liveness(forged, ROOT)
    with pytest.raises(VERIFIER_ERROR):
        verifier.verify_dependency_vector_cut_liveness(forged, ROOT)


def test_every_false_claim_forgery_is_rejected_after_reroot(
    candidate: dict[str, object]
) -> None:
    for field in producer._FALSE_CLAIMS:
        forged = deepcopy(candidate)
        forged[field] = True
        forged["theorem"][field] = True
        forged = _reroot_candidate(forged)
        with pytest.raises(PRODUCER_ERROR):
            producer.validate_dependency_vector_cut_liveness(forged, ROOT)
        with pytest.raises(VERIFIER_ERROR, match="claim|schema|candidate"):
            verifier.verify_dependency_vector_cut_liveness(forged, ROOT)


def test_candidate_and_verification_loaders_require_exact_canonical_bytes(
    tmp_path: Path,
    candidate: dict[str, object],
    verification: dict[str, object],
) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_raw = producer.canonical_document_bytes(candidate)
    candidate_path.write_bytes(candidate_raw)
    assert producer.load_dependency_vector_cut_liveness(candidate_path, ROOT) == candidate
    candidate_path.write_bytes(candidate_raw + b"\n")
    with pytest.raises(PRODUCER_ERROR, match="canonical|decode"):
        producer.load_dependency_vector_cut_liveness(candidate_path, ROOT)

    verification_path = tmp_path / "verification.json"
    verification_raw = verifier.canonical_verification_bytes(verification)
    verification_path.write_bytes(verification_raw)
    assert verifier.load_dependency_vector_cut_liveness_verification(
        verification_path
    ) == verification
    verification_path.write_bytes(verification_raw + b"\n")
    with pytest.raises(VERIFIER_ERROR, match="canonical|decode"):
        verifier.load_dependency_vector_cut_liveness_verification(
            verification_path
        )


def test_strict_json_loaders_reject_duplicate_float_and_nonfinite_numbers(
    tmp_path: Path,
) -> None:
    bad_values = (
        b'{"x":1,"x":2}\n',
        b'{"x":1.5}\n',
        b'{"x":NaN}\n',
        b"\xff\n",
    )
    for index, raw in enumerate(bad_values):
        path = tmp_path / f"bad-{index}.json"
        path.write_bytes(raw)
        with pytest.raises(PRODUCER_ERROR, match="decode"):
            producer.load_dependency_vector_cut_liveness(path, ROOT)
        with pytest.raises(VERIFIER_ERROR, match="decode"):
            verifier.load_dependency_vector_cut_liveness_verification(path)


def _swap_path_during_read(module: object, tmp_path: Path) -> None:
    path = tmp_path / "race.bin"
    path.write_bytes(b"authenticated")
    replacement = tmp_path / "replacement.bin"
    replacement.write_bytes(b"substituted")
    original_read = module.os.read
    swapped = False

    def racing_read(descriptor: int, count: int) -> bytes:
        nonlocal swapped
        raw = original_read(descriptor, count)
        if not swapped:
            swapped = True
            path.rename(tmp_path / "opened-original.bin")
            replacement.rename(path)
        return raw

    module.os.read = racing_read
    try:
        reader = getattr(module, "_read_regular_bytes", None)
        if reader is None:
            reader = getattr(module, "_read_regular", None)
        if reader is None:
            reader = getattr(module, "_safe_regular_bytes")
        with pytest.raises(Exception, match="changed|inspected|identity"):
            reader(path, label="TOCTOU fixture", limit=1024)
    finally:
        module.os.read = original_read


def test_producer_reader_rejects_path_replacement_after_open(tmp_path: Path) -> None:
    _swap_path_during_read(producer, tmp_path)


def test_cli_reader_rejects_path_replacement_after_open(tmp_path: Path) -> None:
    _swap_path_during_read(_load_cli(), tmp_path)


def test_verifier_reader_rejects_path_replacement_after_open(tmp_path: Path) -> None:
    _swap_path_during_read(verifier, tmp_path)
