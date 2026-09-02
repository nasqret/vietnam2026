#!/usr/bin/env python3
"""Source-only inspection of the frozen119 polynomial rows for v34 planning.

No proof, Alpha admission, file installation or publication is performed.
"""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/arithmetic-library/working/prime-field-gcd-closure-v1'))

def main():
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    import working_gcd_closure_support as source
    state = source.load_candidate_state()
    source.require_registration()
    result = []
    offset = 0
    for owner in source.prior.FACTORIES:
        count = owner.count
        rows = state.rows[offset:offset+count]
        offset += count
        record = asdict(owner)
        path = ROOT / owner.directory / (owner.module + '.py')
        raw = path.read_bytes()
        result.append(dict(module=owner.module, factory=owner.factory, path=str(path.relative_to(ROOT)),
            source_bytes=len(raw), source_sha256=sha256(raw).hexdigest(), count=count,
            specs_sha256=source.closure._specs_digest(rows), names=[row.name for row in rows],
            original=record))
    for (label, directory, short), pin, (_, count, expected) in zip(source.FAMILIES, source.FROZEN_SOURCE_PINS, source.COMPONENT_SPECS, strict=True):
        rows = state.rows[offset:offset+count]
        offset += count
        digest = source.closure._specs_digest(rows)
        assert digest == expected
        result.append(dict(module=short, factory='make_'+short+'_theorems', path=pin.path,
            source_bytes=pin.bytes, source_sha256=pin.sha256, count=count, specs_sha256=digest,
            names=[row.name for row in rows], original={'source':asdict(pin)}))
    assert offset == len(state.rows) == 119 and len(result) == 20
    assert sum(item['count'] for item in result) == 119
    selected = source.select_support(state)
    assert len(selected.complete_specs) == 492 and len(selected.support) == 373
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        peak *= 1024
    assert peak <= 1536 * 1024 * 1024
    print(json.dumps(dict(schema='alpha-v34-gcd-source-planning-v1', proof_calls=0,
        factories=result, count=len(state.rows), names=[row.name for row in state.rows],
        specs_sha256=state.specs_sha256, names_sha256=source.NAMES_SHA256,
        edge_count=sum(len(row.dependencies) for row in state.rows),
        command_count=sum(len(row.script) for row in state.rows),
        principals=list(zip(source.PRINCIPAL_ROOTS, source.PRINCIPAL_STATEMENT_SHA256)),
        maximal_roots=source.FINAL_MAXIMAL_ROOTS,
        complete_specs_sha256=source.closure._specs_digest(selected.complete_specs),
        complete_names=[row.name for row in selected.complete_specs],
        ordered_cone_names_sha256=sha256('\n'.join(row.name for row in selected.complete_specs).encode()).hexdigest(),
        complete_edges=sum(len(row.dependencies) for row in selected.complete_specs),
        seconds=time.monotonic()-started, peak_rss_bytes=peak),sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
