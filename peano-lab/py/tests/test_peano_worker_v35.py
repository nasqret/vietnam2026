"""Explicit Jordan worker additions; no change to worker boot algorithms."""
import ast
from hashlib import sha256
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / 'peano-lab'
NEW_MODULES = ('alpha_enrollment_v35', 'campaign_research_v35_closure', 'editions_v35',
    'research_source_plan_v35', 'jordan_count_uniqueness_candidate', 'jordan_multiplicativity_candidate',
    'jordan_multiplicativity_unique_candidate', 'jordan_prime_power_characterization_candidate',
    'jordan_totient_candidate', 'jordan_unit_modulus_candidate')


@pytest.mark.parametrize('name', NEW_MODULES)
def test_new_jordan_source_is_mounted_once_and_parseable(name):
    relative = 'py/peano_lab/library/' + name + '.py'
    assert (LAB / 'worker.js').read_text().count('"' + relative + '"') == 1
    path = LAB / relative
    assert path.is_file() and not path.is_symlink()
    ast.parse(path.read_text())


def test_worker_adds_only_canonical96_artifact_not_research107():
    worker = (LAB / 'worker.js').read_text()
    name = 'jordan-totient-prime-power-unit-proof-bundle-v1.json'
    assert worker.count('"proof-artifacts/' + name + '"') == 1
    artifact = ROOT / 'research/arithmetic-library/artifacts' / name
    assert artifact.stat().st_size == 1620004
    assert sha256(artifact.read_bytes()).hexdigest() == '9164d35758d1fa15d18ec792a429cbb33fd4c511df5651b9f15d37bececf5ea7'
    assert 'jordan-scaling-prefix-107' not in worker
    paths = re.findall(r'"(proof-artifacts/[^"\n]+\.json)"', worker)
    assert len(paths) == len(set(paths)) == 45


def test_worker_execution_body_is_unchanged():
    source = (LAB / 'worker.js').read_text()
    source = re.sub(r'const PY_FILES = \[[\s\S]*?\n\];', 'const PY_FILES = [];', source)
    source = re.sub(r'const PROOF_ARTIFACT_FILES = \[[\s\S]*?\n\];', 'const PROOF_ARTIFACT_FILES = [];', source)
    assert sha256(source.encode()).hexdigest() == '54ab094b461a5161fe4dce4c0e5f6a1b10af1239fb907b556d684288e79de4a7'
