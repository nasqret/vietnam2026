"""V34 explicit browser inventory. Source and Node simulation, not browser/proof evidence."""
from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "peano-lab"
WORKER = LAB / "worker.js"
NEW_MODULES = (
    "py/peano_lab/library/alpha_enrollment_v34.py",
    "py/peano_lab/library/campaign_research_v34_closure.py",
    "py/peano_lab/library/editions_v34.py",
    "py/peano_lab/library/linear_congruence_classification_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_aligned_add_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_aligned_algebra_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_aligned_distributivity_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_alignment_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_append_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_associativity_induction_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_associativity_step_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_bezout_backward_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_divisibility_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_euclidean_identity_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_euclidean_normalization_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_euclidean_transport_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_gcd_bezout_laws_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_gcd_existence_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_gcd_uniqueness_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_left_constant_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_left_unit_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_scalar_convolution_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_shift_candidate.py",
    "py/peano_lab/library/prime_field_polynomial_shift_equivalence_candidate.py",
    "py/peano_lab/library/research_source_plan_v34.py",
)
ARTIFACTS = (
    ("proof-artifacts/prime-field-polynomial-gcd-bezout-proof-bundle-v1.json", 5193292, "3fe18ad2899cff7db5fbe19df8570ef70b1bfb902171d5212e9b036dda660a46"),
    ("proof-artifacts/linear-congruence-classification-proof-bundle-v1.json", 542092, "983051afddc637a4e033546b8f3ddb8dc0ac22aa996b4e28b3822be8895576ad"),
)


def test_only_explicit_inventory_changed_not_worker_execution_or_fetch_algorithms():
    source=WORKER.read_text()
    source=re.sub(r"const PY_FILES = \[[\s\S]*?\n\];","const PY_FILES = [];",source)
    source=re.sub(r"const PROOF_ARTIFACT_FILES = \[[\s\S]*?\n\];","const PROOF_ARTIFACT_FILES = [];",source)
    assert sha256(source.encode()).hexdigest()=="54ab094b461a5161fe4dce4c0e5f6a1b10af1239fb907b556d684288e79de4a7"


@pytest.mark.parametrize("relative",NEW_MODULES)
def test_every_new_canonical_source_is_explicitly_mounted_once(relative):
    assert WORKER.read_text().count('"'+relative+'"')==1
    path=LAB/relative
    assert path.is_file() and not path.is_symlink()
    ast.parse(path.read_text())
    assert "working/" not in relative


@pytest.mark.parametrize("relative,size,digest",ARTIFACTS)
def test_both_case_sensitive_artifact_urls_are_actual_canonical_bundles(relative,size,digest):
    assert WORKER.read_text().count('"'+relative+'"')==1
    path=ROOT/"research/arithmetic-library/artifacts"/Path(relative).name
    assert path.stat().st_size==size and not path.is_symlink()
    with path.open("rb") as stream:
        result=sha256()
        while block:=stream.read(1024*1024): result.update(block)
    assert result.hexdigest()==digest


def test_whole_python_and_artifact_inventories_are_unique_and_reproducible():
    source=WORKER.read_text()
    paths=re.findall(r'"(py/[^"\n]+\.py)"',source)
    actual=sorted(path.relative_to(LAB).as_posix() for path in (LAB/"py/peano_lab").rglob("*.py"))
    assert paths==[*actual,"py/driver.py"] and len(paths)==len(set(paths))
    artifacts=re.findall(r'"(proof-artifacts/[^"\n]+\.json)"',source)
    assert len(artifacts)==len(set(artifacts))==44
    assert artifacts[-2:]==[row[0] for row in ARTIFACTS]
    result=subprocess.run(["python3","-B",str(ROOT/"scripts/update_peano_worker_sources.py"),"--check"],
        capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr


def test_original_node_boot_contract_with_new_real_inventory():
    # This is the unchanged mocked-Pyodide Node VM, not an actual browser,
    # kernel execution, Lean compilation, network fetch or admission.
    result=subprocess.run(["node",str(Path(__file__).with_name("worker_boot_harness.js")),str(WORKER)],
        capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
