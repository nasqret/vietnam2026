"""Genuine constructive Peano certificates become completed Lean theorems."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from peano_lab.kernel.checker import axiom_formula
from peano_lab.kernel.formulas import And, Bot, Eq, Imp, parse_formula
from peano_lab.kernel.proofs import (
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
)
from peano_lab.kernel.terms import Succ, Var, Zero
from peano_lab.library.lean import formula_to_lean
from peano_lab.library.lean_certified import (
    LeanCertificateError,
    _CertificateEmitter,
    export_checked_bundle_theorem,
    export_checked_theorem,
)
from peano_lab.library.proof_bundle import BundleNode, ProofBundle, encode_proof_bundle
from peano_lab.library.theorems import get, replay


ZERO = Zero()
ONE = Succ(ZERO)
P = Eq(ZERO, ZERO)
Q = Eq(ONE, ONE)
ROOT = Path(__file__).resolve().parents[3]
LEAN_PROJECT = ROOT.parent / "peano-lab-lean"
TOOLCHAINS = Path.home() / ".elan" / "toolchains"


def _toolchain_version(path: Path) -> tuple[int, int, int, int]:
    match = re.search(
        r"v(\d+)\.(\d+)\.(\d+)(?:-rc(\d+))?$",
        path.parent.parent.name,
    )
    if match is None:
        return (-1, -1, -1, -1)
    major, minor, patch, candidate = match.groups()
    return (
        int(major),
        int(minor),
        int(patch),
        10_000 if candidate is None else int(candidate),
    )


LAKE_BINARIES = (
    tuple(sorted(TOOLCHAINS.glob("*/bin/lake"), key=_toolchain_version, reverse=True))
    if TOOLCHAINS.is_dir()
    else ()
)


def _compile_with_installed_lean(
    module: Path,
    *,
    memory_mib: str = "1024",
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    # Use the same installed compiler against the already-built companion,
    # without refreshing its Lake cache or installing its pinned toolchain.
    environment = dict(os.environ)
    previous_path = environment.get("LEAN_PATH", "")
    environment["LEAN_PATH"] = str(LEAN_PROJECT / ".lake" / "build" / "lib" / "lean") + (
        os.pathsep + previous_path if previous_path else ""
    )
    return subprocess.run(
        [str(LAKE_BINARIES[0].with_name("lean")), "-M", memory_mib, "-j", "1", str(module)],
        cwd=LEAN_PROJECT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.mark.parametrize(
    "name", ("zero_add", "add_comm", "mul_eq_zero", "mul_comm", "prime_unbounded")
)
def test_real_public_theorems_export_complete_deterministic_certificates(name: str) -> None:
    checked = replay(name)
    specification = get(name)
    assert specification is not None

    exported = export_checked_theorem(
        name,
        checked.formula,
        checked.certificate,
        specification.script,
        dependencies=specification.dependencies,
    )

    assert exported.statement == formula_to_lean(checked.formula)
    assert exported.code.startswith("-- Automatically translated")
    assert "import PeanoLab.Codec" in exported.code
    assert "PeanoLab.Artifact.check_sound accepted" in exported.code
    assert "    decide" in exported.code
    assert "  exact sound (fun _ => 0)" in exported.code
    assert "  simpa [" not in exported.code
    assert f"#print axioms «{name}»" in exported.code
    assert exported.live_url == ""
    assert re.search(
        r"\bsorry\b|\bnative_decide\b|^\s*axiom\s+",
        exported.code,
        re.MULTILINE,
    ) is None
    assert exported == export_checked_theorem(
        name,
        checked.formula,
        checked.certificate,
        specification.script,
        dependencies=specification.dependencies,
    )


@pytest.mark.parametrize(
    ("proof", "tag"),
    (
        (Hyp(0), "hyp"),
        (ImpIntro(Hyp(0)), "impIntro"),
        (ImpElim(Hyp(0), Hyp(1)), "impElim"),
        (Cut(P, Q, EqRefl(ZERO), EqRefl(ONE)), "cut"),
        (AndIntro(Hyp(0), Hyp(1)), "andIntro"),
        (AndElimL(Hyp(0)), "andElimL"),
        (AndElimR(Hyp(0)), "andElimR"),
        (OrIntroL(Hyp(0)), "orIntroL"),
        (OrIntroR(Hyp(0)), "orIntroR"),
        (OrElim(Hyp(0), Hyp(1), Hyp(2)), "orElim"),
        (BotElim(Hyp(0)), "botElim"),
        (ForallIntro(Hyp(0)), "forallIntro"),
        (ForallElim(Hyp(0), ZERO), "forallElim"),
        (ExistsIntro(ZERO, Hyp(0)), "existsIntro"),
        (ExistsElim(Hyp(0), Hyp(1)), "existsElim"),
        (EqRefl(ZERO), "eqRefl"),
        (EqSym(Hyp(0)), "eqSym"),
        (EqTrans(Hyp(0), Hyp(1)), "eqTrans"),
        (CongS(Hyp(0)), "congS"),
        (CongAdd(Hyp(0), Hyp(1)), "congAdd"),
        (CongMul(Hyp(0), Hyp(1)), "congMul"),
        (EqSubst(Eq(Var(0), ZERO), Hyp(0), Hyp(1)), "eqSubst"),
        (Axiom("PA1"), "axiom"),
        (Ind(Eq(Var(0), Var(0)), EqRefl(ZERO), Hyp(0)), "ind"),
    ),
)
def test_every_constructive_proof_constructor_has_an_exact_lean_encoding(
    proof: object,
    tag: str,
) -> None:
    emitter = _CertificateEmitter("all_constructors")

    emitter.proof(proof)  # type: ignore[arg-type]

    assert any(f".{tag} " in declaration for declaration in emitter.declarations)


@pytest.mark.parametrize("name", ("PA1", "PA2", "PA3", "PA4", "PA5", "PA6"))
def test_only_the_six_actual_arithmetic_axioms_are_translated(name: str) -> None:
    formula = axiom_formula(name)
    assert formula is not None

    exported = export_checked_theorem(name.lower(), formula, Axiom(name))

    assert f".axiom .{name.lower()}" in exported.code


def test_structurally_identical_subproofs_and_formulas_are_shared_once() -> None:
    left = EqRefl(Zero())
    right = EqRefl(Zero())
    target = And(P, P)
    exported = export_checked_theorem("shared_reflexivity", target, AndIntro(left, right))

    proof_definitions = [
        line
        for line in exported.code.splitlines()
        if line.startswith("private def ") and " : PeanoLab.Proof := " in line
    ]

    assert len(proof_definitions) == 2
    assert exported.code.count(" : PeanoLab.Term := .zero") == 1
    assert exported.code.count(" : PeanoLab.Formula := .eq ") == 1


def _shared_proof_bundle() -> ProofBundle:
    return ProofBundle(
        nodes=(
            BundleNode(10, P, (), EqRefl(ZERO)),
            BundleNode(
                30,
                And(P, P),
                (10,),
                ImpIntro(AndIntro(Hyp(0), Hyp(0))),
            ),
        ),
        root=30,
    )


def _quantified_shared_export(*, bundle: bool):
    # Several private Formula aliases lie below both universal binders.
    # The semantic boundary also crosses implication, conjunction, existential
    # quantification and disjunction; it must not depend on simp unfolding
    # only the single outermost Formula definition.
    target = parse_formula(
        r"forall a b. (a = a /\ b = b) -> ((exists c. c = a) \/ b = b)"
    )
    proof = ForallIntro(
        ForallIntro(ImpIntro(OrIntroL(ExistsIntro(Var(1), EqRefl(Var(1))))))
    )
    if bundle:
        return export_checked_bundle_theorem(
            "quantified_shared_bundle",
            ProofBundle((BundleNode(0, target, (), proof),), root=0),
            target,
        )
    return export_checked_theorem("quantified_shared_certificate", target, proof)


@pytest.mark.parametrize("bundle", (False, True), ids=("certificate", "bundle"))
def test_shared_quantifier_children_use_exact_semantic_conversion(bundle: bool) -> None:
    exported = _quantified_shared_export(bundle=bundle)

    assert exported.code.count(" : PeanoLab.Formula := .forallE ") == 2
    assert " : PeanoLab.Formula := .existsE " in exported.code
    assert " : PeanoLab.Formula := .imp " in exported.code
    assert " : PeanoLab.Formula := .conj " in exported.code
    assert " : PeanoLab.Formula := .disj " in exported.code
    assert exported.code.count("  exact sound (fun _ => 0)") == 1
    assert "  simpa [" not in exported.code
    assert "    decide" in exported.code
    assert f"#print axioms «{exported.name}»" in exported.code
    assert re.search(r"\bsorry\b|\bnative_decide\b|^\s*axiom\s+", exported.code, re.M) is None


def test_shared_checked_bundle_exports_a_complete_dense_lean_theorem() -> None:
    target = And(P, P)
    exported = export_checked_bundle_theorem("shared_bundle", _shared_proof_bundle(), target)

    assert exported.statement == "0 = 0 ∧ 0 = 0"
    assert "import PeanoLab.ProofBundle" in exported.code
    assert "PeanoLab.checkBundle_sound accepted" in exported.code
    assert "  exact sound (fun _ => 0)" in exported.code
    assert "  simpa [" not in exported.code
    assert "dependencies := [0]" in exported.code
    assert "root := 1" in exported.code
    assert "sorry" not in exported.code
    assert exported.live_url == ""


def test_false_or_wrong_target_proof_bundles_cannot_become_lean_theorems() -> None:
    with pytest.raises(LeanCertificateError, match="complete proof bundle"):
        export_checked_bundle_theorem("wrong_target", _shared_proof_bundle(), P)
    corrupted = ProofBundle(
        nodes=(BundleNode(0, Eq(ZERO, ONE), (), EqRefl(ZERO)),),
        root=0,
    )
    with pytest.raises(LeanCertificateError, match="complete proof bundle"):
        export_checked_bundle_theorem("false_target", corrupted, Eq(ZERO, ONE))


def test_compact_double_and_add_literals_render_as_exact_lean_numerals() -> None:
    target = parse_formula("1000000 = 1000000")
    assert type(target) is Eq

    exported = export_checked_theorem("large_numeral", target, EqRefl(target.left))

    assert exported.statement == "1000000 = 1000000"
    assert "theorem «large_numeral» : 1000000 = 1000000 := by" in exported.code
    assert ".mul " in exported.code


def test_false_theorems_and_wrong_targets_fail_at_the_original_kernel() -> None:
    with pytest.raises(LeanCertificateError, match="original closed theorem"):
        export_checked_theorem("false_theorem", Eq(ZERO, ONE), EqRefl(ZERO))

    checked = replay("zero_add")
    with pytest.raises(LeanCertificateError, match="original closed theorem"):
        export_checked_theorem("wrong_target", P, checked.certificate)


def test_classical_double_negation_cannot_enter_a_constructive_lean_theorem() -> None:
    target = Imp(Imp(Imp(P, Bot()), Bot()), P)

    with pytest.raises(LeanCertificateError, match="original closed theorem"):
        export_checked_theorem("classical_intrusion", target, DNE(P))
    with pytest.raises(LeanCertificateError, match="classical double-negation"):
        _CertificateEmitter("classical_intrusion").proof(DNE(P))


@pytest.mark.parametrize("name", ("", "_", "9bad", "x; #check False", "two words"))
def test_unsafe_declaration_and_dependency_names_are_rejected(name: str) -> None:
    with pytest.raises(ValueError, match="ASCII identifier"):
        export_checked_theorem(name, P, EqRefl(ZERO))
    with pytest.raises(ValueError, match="ASCII identifier"):
        export_checked_theorem("safe", P, EqRefl(ZERO), dependencies=(name,))


def test_audit_and_dependency_contracts_are_fail_closed() -> None:
    with pytest.raises(TypeError, match="boolean"):
        export_checked_theorem("safe", P, EqRefl(ZERO), include_axiom_audit=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="dependencies"):
        export_checked_theorem("safe", P, EqRefl(ZERO), dependencies="oops")  # type: ignore[arg-type]

    exported = export_checked_theorem("safe", P, EqRefl(ZERO), include_axiom_audit=False)
    assert "#print axioms" not in exported.code


@pytest.mark.skipif(
    not LAKE_BINARIES or not (LEAN_PROJECT / "PeanoLab" / "Codec.lean").is_file(),
    reason="the independent sibling Lean companion or installed Lake is unavailable",
)
@pytest.mark.parametrize(
    "name", ("zero_add", "add_comm", "mul_eq_zero", "mul_comm", "prime_unbounded")
)
def test_independent_lean_compiler_accepts_real_completed_public_theorems(
    name: str,
    tmp_path: Path,
) -> None:
    checked = replay(name)
    exported = export_checked_theorem(name, checked.formula, checked.certificate)
    module = tmp_path / f"{name}.lean"
    module.write_text(exported.code + "\n", encoding="utf-8")
    memory_mib = "1536" if name == "prime_unbounded" else "1024"

    result = _compile_with_installed_lean(module, memory_mib=memory_mib)

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"'PeanoLab.{name}' depends on axioms:" in result.stdout
    assert "sorryAx" not in result.stdout + result.stderr
    assert "Lean.trustCompiler" not in result.stdout + result.stderr


@pytest.mark.skipif(
    not LAKE_BINARIES or not (LEAN_PROJECT / "PeanoLab" / "Codec.lean").is_file(),
    reason="the independent sibling Lean companion or installed Lake is unavailable",
)
def test_independent_lean_compiler_accepts_compact_million_literal(
    tmp_path: Path,
) -> None:
    target = parse_formula("1000000 = 1000000")
    assert type(target) is Eq
    exported = export_checked_theorem("million_reflexivity", target, EqRefl(target.left))
    module = tmp_path / "million_reflexivity.lean"
    module.write_text(exported.code + "\n", encoding="utf-8")

    result = _compile_with_installed_lean(module)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "sorryAx" not in result.stdout + result.stderr
    assert "'PeanoLab.million_reflexivity' depends on axioms:" in result.stdout


@pytest.mark.skipif(
    not LAKE_BINARIES or not (LEAN_PROJECT / "PeanoLab" / "ProofBundle.lean").is_file(),
    reason="the independent sibling Lean bundle companion is unavailable",
)
def test_independent_lean_compiler_accepts_completed_shared_bundle_theorem(
    tmp_path: Path,
) -> None:
    exported = export_checked_bundle_theorem(
        "shared_bundle_theorem",
        _shared_proof_bundle(),
        And(P, P),
    )
    module = tmp_path / "shared_bundle_theorem.lean"
    module.write_text(exported.code + "\n", encoding="utf-8")

    result = _compile_with_installed_lean(module)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "'PeanoLab.shared_bundle_theorem' depends on axioms:" in result.stdout
    assert "sorryAx" not in result.stdout + result.stderr


@pytest.mark.skipif(
    not LAKE_BINARIES or not (LEAN_PROJECT / "PeanoLab" / "ProofBundle.lean").is_file(),
    reason="the independent sibling Lean bundle companion is unavailable",
)
@pytest.mark.parametrize("bundle", (False, True), ids=("certificate", "bundle"))
def test_independent_lean_accepts_semantic_conversion_below_shared_quantifiers(
    bundle: bool,
    tmp_path: Path,
) -> None:
    exported = _quantified_shared_export(bundle=bundle)
    module = tmp_path / f"{exported.name}.lean"
    module.write_text(exported.code + "\n", encoding="utf-8")
    result = _compile_with_installed_lean(module, timeout=35)

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"'PeanoLab.{exported.name}' depends on axioms:" in result.stdout
    assert "sorryAx" not in result.stdout + result.stderr
    assert "Lean.trustCompiler" not in result.stdout + result.stderr


def test_converter_cli_rejects_unknown_theorems_and_existing_output(tmp_path: Path) -> None:
    cli = ROOT / "scripts" / "export_peano_lean.py"
    missing = subprocess.run(
        [sys.executable, "-B", str(cli), "not_a_public_theorem"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert missing.returncode == 2
    assert "Unknown public Peano theorem" in missing.stderr

    existing = tmp_path / "preserved.lean"
    existing.write_text("preserve this user content\n", encoding="utf-8")
    protected = subprocess.run(
        [sys.executable, "-B", str(cli), "zero_add", "--output", str(existing)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert protected.returncode == 1
    assert "already exists" in protected.stderr
    assert existing.read_text(encoding="utf-8") == "preserve this user content\n"


@pytest.mark.parametrize(
    "name",
    (
        "linear_congruence_solvable_iff_gcd_divides",
        "infinitely_many_primes_one_mod_four",
        "prime_is_two_squares_iff_two_or_one_mod_four",
        "pythagorean_primitive_normal_form",
        "prime_power_valuation_exists",
    ),
)
def test_converter_cli_recognizes_new_checked_alpha_v19_goals_without_proof_replay(
    name: str,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "export_peano_lean.py"),
            name,
            "--edition",
            "alpha",
            "--format",
            "pretty",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert name in result.stdout
    assert "Preview only: no fresh kernel or Lean proof replay." in result.stderr
    assert "Independent Lean compilation: PASSED" not in result.stdout + result.stderr


def test_converter_cli_rejects_wrong_synthetic_bundle_for_named_alpha_v19_goal(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "wrong-alpha-root.json"
    artifact.write_text(
        encode_proof_bundle(_shared_proof_bundle(), And(P, P)),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "export_peano_lean.py"),
            "linear_congruence_solvable_iff_gcd_divides",
            "--edition",
            "alpha",
            "--proof-bundle",
            str(artifact),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "target disagrees with the named public theorem" in result.stderr


def test_converter_cli_translates_checked_bundle_without_registry_authority(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "bundle.json"
    artifact.write_text(
        encode_proof_bundle(_shared_proof_bundle(), And(P, P)),
        encoding="utf-8",
    )
    destination = tmp_path / "bundle.lean"
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "export_peano_lean.py"),
            "independent_shared_theorem",
            "--proof-bundle",
            str(artifact),
            "--output",
            str(destination),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 independently checked bundle nodes" in result.stderr
    assert "theorem «independent_shared_theorem» : 0 = 0 ∧ 0 = 0" in (
        destination.read_text(encoding="utf-8")
    )


def test_converter_cli_rejects_bundles_mismatching_named_public_theorems(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "wrong-target.json"
    artifact.write_text(
        encode_proof_bundle(_shared_proof_bundle(), And(P, P)),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "export_peano_lean.py"),
            "zero_add",
            "--proof-bundle",
            str(artifact),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "target disagrees with the named public theorem" in result.stderr


@pytest.mark.parametrize(
    ("arguments", "message"),
    (
        (("--max-memory-mib", "0"), "memory bound"),
        (("--max-memory-mib", "16385"), "memory bound"),
        (("--max-verify-seconds", "0"), "verification timeout"),
        (("--max-verify-seconds", "3601"), "verification timeout"),
    ),
)
def test_converter_cli_rejects_unbounded_or_unsafe_verification_limits(
    arguments: tuple[str, str],
    message: str,
) -> None:
    cli = ROOT / "scripts" / "export_peano_lean.py"
    result = subprocess.run(
        [sys.executable, "-B", str(cli), "zero_add", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert message in result.stderr


def test_converter_cli_terminates_the_complete_lean_process_group_on_timeout(
    tmp_path: Path,
) -> None:
    project = tmp_path / "lean-project"
    codec = project / "PeanoLab" / "Codec.lean"
    codec.parent.mkdir(parents=True)
    codec.write_text("-- fake project for isolated watchdog testing\n", encoding="utf-8")
    lake = tmp_path / "fake-lake"
    lake.write_text("#!/bin/sh\nsleep 60 &\nwait\n", encoding="utf-8")
    lake.chmod(0o700)
    destination = tmp_path / "guarded.lean"

    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "export_peano_lean.py"),
            "zero_add",
            "--output",
            str(destination),
            "--verify",
            "--lean-project",
            str(project),
            "--lake",
            str(lake),
            "--max-verify-seconds",
            "1",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "exceeded its 1-second limit" in result.stderr


@pytest.mark.parametrize("forbidden", ("sorryAx", "Lean.trustCompiler"))
def test_converter_cli_rejects_incomplete_or_compiler_trusting_axiom_reports(
    forbidden: str,
    tmp_path: Path,
) -> None:
    project = tmp_path / "lean-project"
    codec = project / "PeanoLab" / "Codec.lean"
    codec.parent.mkdir(parents=True)
    codec.write_text("-- fake project for isolated axiom-audit testing\n", encoding="utf-8")
    lake = tmp_path / "fake-lake"
    lake.write_text(f"#!/bin/sh\nprintf '%s\\n' '{forbidden}'\n", encoding="utf-8")
    lake.chmod(0o700)

    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "export_peano_lean.py"),
            "zero_add",
            "--output",
            str(tmp_path / "rejected.lean"),
            "--verify",
            "--lean-project",
            str(project),
            "--lake",
            str(lake),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert forbidden in result.stderr
