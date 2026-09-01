#!/usr/bin/env python3
"""Original bounded conditional-body diagnostics, never closed acceptance.

Read actual working sources privately and retain their byte identities.
The sealed52 controller and its recursively pinned providers are unchanged.
One invocation checks one chosen native body; no saved report is authority.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
from importlib import import_module, util
import json
from pathlib import Path
import resource
import signal
import sys
import time


ROOT = Path(__file__).resolve().parents[4]
WORKING = ROOT / 'research/arithmetic-library/working'
PRIOR52 = WORKING / 'prime-field-left-unit-closure-v1/working_left_unit_closure_support.py'
PRIOR52_PIN = (31719, 'e1374a8d87915bfd72349b675953e5396043704ddb847e435445cc0451e44fc8')
SOURCES = (
    ('alignment', 'prime-field-alignment-v1', 'prime_field_polynomial_alignment_candidate'),
    ('aligned-add', 'prime-field-aligned-add-v1', 'prime_field_polynomial_aligned_add_candidate'),
    ('aligned-algebra', 'prime-field-aligned-algebra-v1', 'prime_field_polynomial_aligned_algebra_candidate'),
    ('identity', 'prime-field-euclidean-identity-v1', 'prime_field_polynomial_euclidean_identity_candidate'),
    ('distributivity', 'prime-field-aligned-distributivity-v1', 'prime_field_polynomial_aligned_distributivity_candidate'),
    ('transport', 'prime-field-euclidean-transport-v1', 'prime_field_polynomial_euclidean_transport_candidate'),
    ('bezout', 'prime-field-bezout-backward-v1', 'prime_field_polynomial_bezout_backward_candidate'),
)
PROVIDERS = (
    'prime_field_polynomial_subtraction_candidate', 'prime_field_polynomial_degree_candidate',
    'prime_field_polynomial_monic_candidate', 'prime_field_polynomial_trim_candidate',
    'prime_field_polynomial_division_candidate',
)


def pin(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError('diagnostics require actual regular source files')
    raw = path.read_bytes()
    return len(raw), sha256(raw).hexdigest()


def load_private(path, name, *, controller=False):
    if name in sys.modules:
        raise ValueError('a private diagnostic module name is already owned')
    specification = util.spec_from_file_location(name, path)
    module = util.module_from_spec(specification)
    if controller:
        sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
        return module
    finally:
        if controller:
            if sys.modules.get(name) is not module:
                raise ValueError('a changed foreign module binding must be preserved')
            del sys.modules[name]


def main(argv=None):
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=tuple(item[0] for item in SOURCES), required=True)
    parser.add_argument('--index', type=int, required=True)
    args = parser.parse_args(argv)
    for directory in (ROOT / 'peano-lab/py', ROOT / 'scripts'):
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
    assert pin(PRIOR52) == PRIOR52_PIN
    parent = load_private(PRIOR52, '_working_euclidean_development_prior52', controller=True)
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    from peano_lab.library.theorems import TheoremSpec
    core = parent.canonical_provider_table()
    for short in PROVIDERS:
        module = import_module('peano_lab.library.' + short)
        for row in getattr(module, 'make_' + short + '_theorems')(TheoremSpec):
            assert row.name not in core or core[row.name] == row
            core[row.name] = row
    for row in parent.load_candidate_state().rows:
        assert row.name not in core
        core[row.name] = row
    paths, selected = [], None
    for family, directory, short in SOURCES:
        path = WORKING / directory / (short + '.py')
        paths.append(path)
        module = load_private(path, '_working_euclidean_development_' + short)
        rows = getattr(module, 'make_' + short + '_theorems')(TheoremSpec)
        for row in rows:
            assert row.name not in core
            core[row.name] = row
        if family == args.family:
            assert 0 <= args.index < len(rows)
            selected = rows[args.index]
    assert selected is not None
    pins = {path.relative_to(ROOT).as_posix(): pin(path) for path in paths}
    protected = parent._edition_bindings()
    print(json.dumps({'kind': 'conditional-body-inputs', 'source_pins': pins,
                      'row': selected.name, 'commands': len(selected.script),
                      'dependencies': list(selected.dependencies)}), flush=True)
    try:
        receipt = replay_candidate_bodies((selected,), core=core)[0]
        print(json.dumps({'kind': 'conditional-body-result', **asdict(receipt)}, sort_keys=True), flush=True)
    finally:
        assert pins == {path.relative_to(ROOT).as_posix(): pin(path) for path in paths}
        assert pin(PRIOR52) == PRIOR52_PIN
        parent.require_runtime_sources()
        parent.require_working_sources()
        after = parent._edition_bindings()
        assert after.keys() == protected.keys() and all(after[key] is value for key, value in protected.items())
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert peak <= 1536 * 1024 * 1024
        assert resource.getrlimit(resource.RLIMIT_CPU) == (170, 175)
        print(json.dumps({'kind': 'conditional-body-resources',
                          'elapsed_seconds': time.monotonic() - started, 'peak_rss_bytes': peak,
                          'cpu_limits': [170, 175], 'wall_alarm_seconds': 180,
                          'conditional_only': True, 'complete_cone_checked': False,
                          'lean_checked': False, 'admission_performed': False}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
