"""Compile the exact new reading-policy Lean bodies with the pinned compiler.

The library pilots below quantify their original dependency statements as
explicit theorem parameters. They validate dependency-relative translation,
not a fresh admission or a replacement for full dependency-strand checks.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

from peano_lab.kernel.formulas import parse_formula
from peano_lab.library.lean_presentation import readable_formula
from peano_lab.library.lean_proof_reconstruction import reconstruct_theorem
from peano_lab.library.lean_proof_strand import _live_definitions
from peano_lab.library.theorems import TheoremSpec, get


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py/tests"))
from test_inferred_have import EXAMPLES


@pytest.fixture(scope="module")
def compiler():
    source = importlib.util.spec_from_file_location(
        "reading_policy_lean_exporter", ROOT / "scripts/export_peano_lean.py"
    )
    assert source is not None and source.loader is not None
    exporter = importlib.util.module_from_spec(source)
    source.loader.exec_module(exporter)
    project = ROOT.parent / "peano-lab-lean"
    lake = exporter._lake_binary(project, None)
    lean = lake.with_name("lean")
    version = subprocess.run(
        [str(lean), "--version"], check=True, capture_output=True, text=True, timeout=10
    ).stdout
    assert re.search(r"\bversion 4\.31\.0(?:,|\s)", version), version
    return lean, exporter


def compile_body(compiler, tmp_path, specification, formulas=None):
    lean, exporter = compiler
    formulas = formulas or {}
    references = {
        name: f"reader_dependency_{index}"
        for index, name in enumerate(specification.dependencies)
    }
    result = reconstruct_theorem(
        specification,
        dependency_references=references,
        dependency_formulas=formulas,
    )
    assert result.status == "translated", result.diagnostics
    assert result.translated_steps == len(specification.script)
    assert "have " in result.lean_body and " := " in result.lean_body
    # Production dependencies are separately declared closed constants. Keep
    # their large closed types shared here too: copying every expanded type
    # beneath the test's extra proof-parameter binders is not that interface.
    propositions = "\n".join(
        f"def reader_proposition_{index} : Prop := {readable_formula(formulas[name])}"
        for index, name in enumerate(specification.dependencies)
    )
    parameters = "".join(
        f" ({references[name]} : reader_proposition_{index})"
        for index, name in enumerate(specification.dependencies)
    )
    declarations = f"{propositions}\n{result.lean_statement}\n{result.lean_body}"
    definitions = "\n".join(_live_definitions(set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", declarations))))
    content = (
        "-- Match the production import-free standalone Lean surface.\n"
        "set_option autoImplicit false\n"
        "set_option maxRecDepth 4096\nset_option maxHeartbeats 800000\n"
        f"{definitions}\n"
        f"{propositions}\n"
        f"def reader_target : Prop := {result.lean_statement}\n"
        f"theorem reading_policy_check{parameters} : reader_target :=\n"
        f"{result.lean_body}\n#print axioms reading_policy_check\n"
        f"example{parameters} : {result.lean_statement} := "
        f"reading_policy_check {' '.join(references.values())}\n"
    )
    assert re.search(r"\bsorry\b|\badmit\b|\bnative_decide\b|^\s*axiom\s+", content, re.M) is None
    path = tmp_path / "ReadingPolicy.lean"
    path.write_text(content, encoding="utf-8")
    exporter._require_lean_verifier_source_budget(path, max_memory_mib=1024)
    process = subprocess.run(
        [str(lean), "-M", "1024", "-j", "1", str(path)],
        cwd=tmp_path, capture_output=True, text=True, timeout=90,
    )
    output = process.stdout + process.stderr
    assert process.returncode == 0, output
    assert "does not depend on any axioms" in output, output
    assert "sorryAx" not in output and "Lean.trustCompiler" not in output
    return result


@pytest.mark.parametrize("statement,script", EXAMPLES)
def test_native_inferred_applications_compile_in_lean(compiler, tmp_path, statement, script):
    compile_body(compiler, tmp_path,
        TheoremSpec("reading_application", statement, (), script, "Compiler regression."))


LEGACY_CASES = (
    ("forall n. n = 0 -> n = 0",
     ("intro n", "intro hn", "have h : n = 0", "exact hn", "exact h")),
    ("(0 = 0 -> 1 = 1 -> 2 = 2) -> 2 = 2",
     ("intro lemma", "have ha : 0 = 0", "refl", "have hb : 1 = 1", "refl",
      "have h : 2 = 2", "apply lemma", "exact ha", "exact hb", "exact h")),
    ("0 = 0 -> forall n. 0 = 0",
     ("intro lemma", "induction n", "have hz : 0 = 0", "exact lemma", "exact hz",
      "have hs : 0 = 0", "exact lemma", "exact hs")),
    ("forall n. (forall x. x = 0 -> S x = 1) -> n = 0 -> S n = 1",
     ("intro n", "intro lemma", "intro hn", "have h : S n = 1",
      "specialize lemma n", "apply lemma", "exact hn", "exact h")),
    ("forall n. (forall x. x = x) -> (n = n /\\ S n = S n)",
     ("intro n", "intro lemma", "have h : n = n", "specialize lemma n", "exact lemma",
      "split", "exact h", "have second := lemma (S n)", "exact second")),
)


@pytest.mark.parametrize("statement,script", LEGACY_CASES)
def test_shortened_legacy_claims_compile_with_their_original_scopes(
    compiler, tmp_path, statement, script,
):
    result = compile_body(compiler, tmp_path,
        TheoremSpec("reading_legacy", statement, (), script, "Compiler regression."))
    assert result.inferred_claims >= 1


@pytest.mark.parametrize("family,theorem", (
    ("two-squares", "two_square_iff_zero_or_even_three_mod_four_prime_valuations"),
    ("binary-digit-extraction", "binary_modular_execution_logarithmic_bound"),
    ("euclidean-logarithmic-bound", "euclidean_log_budget_extend_twice"),
))
def test_long_library_bodies_compile_under_explicit_original_dependencies(
    compiler, tmp_path, family, theorem,
):
    path = ROOT / "_deploy/proofs-public-v1" / family / "api/corpus.json"
    if not path.is_file():
        pytest.skip("preserved public corpus is not available")
    original = path.read_bytes()
    rows = {row["name"]: row for row in json.loads(original)["nodes"]}
    row = rows[theorem]
    specification = TheoremSpec(
        theorem, row["statement"], tuple(row["dependencies"]),
        tuple(row["script"]), row["summary"],
    )
    formulas = {}
    for name in specification.dependencies:
        if name in rows:
            statement = rows[name]["statement"]
        else:
            stable = get(name)
            assert stable is not None, f"missing original dependency {name}"
            statement = stable.statement
        formulas[name] = parse_formula(statement)
    result = compile_body(compiler, tmp_path, specification, formulas)
    assert result.inferred_claims == 2
    assert path.read_bytes() == original
