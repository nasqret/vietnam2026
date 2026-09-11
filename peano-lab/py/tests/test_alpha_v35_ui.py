"""Current Jordan-v35 metadata routes; no proof replay is evidence here."""
from hashlib import sha256
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import driver
import pytest
from peano_lab.library import lean_proof_strand, theorems
from peano_lab.ui import data_library

ROOT = Path(__file__).resolve().parents[3]
PRINCIPALS = ('jordan_totient_multiplicativity_unique_counts', 'jordan_totient_at_one_unique',
              'jordan_prime_power_tuple_primitive_characterization',
              'jordan_prime_power_tuple_primitivity_invariant')


@pytest.fixture(scope='module')
def alpha():
    from peano_lab.library import editions_v35
    return editions_v35


@pytest.fixture(scope='module')
def exporter():
    loader = importlib.util.spec_from_file_location('_v35_selector_export', ROOT / 'scripts/export_peano_lean.py')
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def forbid_proofs(monkeypatch, alpha):
    def forbidden(*_args, **_kwargs):
        raise AssertionError('metadata dispatch tried to replay a theorem or load proof bytes')
    for edition in (alpha, alpha.v34, alpha.v34.v33):
        for name in ('replay', '_checked_research_bundle', 'checked_research_bundle'):
            monkeypatch.setattr(edition, name, forbidden)
        for name in ('read_research_bundle_bytes', 'check_research_proof_bundle'):
            monkeypatch.setattr(edition.research, name, forbidden)
    monkeypatch.setattr(data_library, 'replay', forbidden)
    monkeypatch.setattr(data_library, 'export_checked_theorem', forbidden)
    monkeypatch.setattr(lean_proof_strand, 'build_proof_strand', forbidden)


def test_current_three_selectors_use_exact_v35_and_reuse_stable(alpha, exporter, monkeypatch):
    forbid_proofs(monkeypatch, alpha)
    assert data_library._alpha_edition() is alpha
    assert lean_proof_strand._edition_view('alpha') == (alpha.ALPHA_EDITION, 'v35')
    assert lean_proof_strand._edition_view('stable') == (alpha.STABLE_EDITION, 'stable')
    assert len(alpha.ALPHA_ENTRIES) == 4318 and len(alpha.FRONTIER_NEW_NAMES) == 95
    assert len(alpha.v34.ALPHA_ENTRIES) == 4223
    assert alpha.STABLE_EDITION is alpha.v34.STABLE_EDITION and len(alpha.STABLE_ENTRIES) == 432
    output = driver.LabSession().run('pa lib alpha')
    for expected in ('immutable Alpha v35', 'Enrolled statements: 4,318', 'Alpha closed: 3,886',
                     'Previously added Alpha v34 campaign results: 131', 'New constructive campaign results: 95',
                     alpha.ALPHA_V35_IDENTITY_SHA256):
        assert expected in output
    assert 'kernel check: PASS' not in output
    assert '432 scripted theorems' in driver.LabSession().run('pa lib')
    for name in PRINCIPALS:
        spec, edition = exporter._load_selected_specification(SimpleNamespace(edition='alpha', theorem=name))
        assert edition is alpha and spec is alpha.entry(name, edition='alpha').spec


@pytest.mark.parametrize('name', PRINCIPALS)
def test_exact_jordan_evidence_card_is_replay_free_and_alpha_only(name, alpha, monkeypatch):
    forbid_proofs(monkeypatch, alpha)
    item = alpha.entry(name, edition='alpha')
    assert item.checked_use and alpha.v34.entry(name, edition='alpha') is None
    assert theorems.get(name) is None and alpha.entry(name, edition='stable') is None
    output = driver.LabSession().run('pa lib alpha ' + name)
    assert name + ' — Alpha v35 theorem evidence' in output
    assert 'Release membership: alpha_only' in output and 'Checked-use authority: YES' in output
    assert 'This evidence card does not itself replay a proof.' in output
    assert 'kernel check: PASS' not in output


def test_checked_research107_does_not_silently_enter_the95_promotion(alpha, monkeypatch):
    forbid_proofs(monkeypatch, alpha)
    name = 'jordan_box_divisible_scaling_preimage_exists'
    assert alpha.entry(name, edition='alpha') is None
    assert 'No Alpha v35 theorem' in driver.LabSession().run('pa lib alpha ' + name)


@pytest.mark.parametrize('command', ('pa lib alpha', 'pa lib alpha ' + PRINCIPALS[0],
                                    'pa proof alpha ' + PRINCIPALS[1], 'pa lean alpha ' + PRINCIPALS[2]))
def test_unsealed_current_never_falls_back_to_v34(command, alpha, monkeypatch):
    forbid_proofs(monkeypatch, alpha)
    monkeypatch.setattr(alpha, 'EXPECTED_ALPHA_V35_COUNT', 0)
    monkeypatch.setattr(alpha.v34, 'entry', lambda *_a, **_k: pytest.fail('unsealed selector used historical fallback'))
    output = driver.LabSession().run(command)
    assert 'Alpha v35 is not sealed for checked use' in output
    assert 'Checked-use authority: YES' not in output


def test_v34_admission_source_bytes_remain_literal():
    pins = {
        'editions_v34.py': 'aa5fb0f3189d6beca6a45c51af82ea4b3b001ec164aa79981dcb91813d77ff3a',
        'alpha_enrollment_v34.py': '39acbd725b965b6aaf4d25779b4410755ae862c359b357438f3f7fd80daee468',
        'campaign_research_v34_closure.py': '8741639496d79b8afa6863ac7da0b0087e4ea487f9eddd72eda9461093e9a228',
    }
    for name, expected in pins.items():
        assert sha256((ROOT / 'peano-lab/py/peano_lab/library' / name).read_bytes()).hexdigest() == expected


def test_fresh_stable_boot_does_not_initialize_any_v35_module():
    program = """
import importlib.abc,sys
class ForbidCurrentAlpha(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('peano_lab.library.') and ('_v35' in fullname or 'jordan_' in fullname):
            raise AssertionError('Stable boot initialized current Alpha: '+fullname)
sys.meta_path.insert(0,ForbidCurrentAlpha())
sys.path.insert(0,'peano-lab/py')
import driver
text=driver.LabSession().run('pa lib')
assert '432 scripted theorems' in text
assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)
print('Stable lazy boot PASS')
"""
    result = subprocess.run([sys.executable, '-B', '-c', program], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'Stable lazy boot PASS'
