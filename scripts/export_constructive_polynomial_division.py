#!/usr/bin/env python3
"""Draft G091 polynomial-prerequisite proof-data authoring; never a final release/admission gate."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import resource
import signal
import sys

import constructive_polynomial_division_support as support
from check_constructive_bottom_layers import authoring_rss_bytes

closure = support.closure
CPU_LIMITS = (170,175)
WALL_SECONDS = 180


def export_authoring_bundle(owned_names, output, *, seed_bundles=(), seed_only=False):
    """Only genuine complete ordinary HA proof data is written, exclusively.

    --through and --seed-only affect authoring scheduling, never final checker
    inventory. Every explicitly supplied seed is freshly checked in full by
    the original assembler, even if it contributes no retained body.
    """
    if type(seed_only) is not bool or type(seed_bundles) is not tuple:
        raise support.PolynomialDivisionError('authoring seed options must have exact types')
    if seed_only and not seed_bundles:
        raise support.PolynomialDivisionError('seed-only authoring needs real explicit proof data')
    destination = Path(output)
    allowed = support.ROOT/'research/arithmetic-library/artifacts'
    if not destination.resolve().is_relative_to(allowed.resolve()):
        raise support.PolynomialDivisionError('new proof data must remain inside the task artifact directory')
    if destination.exists() or destination.is_symlink():
        raise support.PolynomialDivisionError('mathematical proof data is never overwritten')
    state = support.load_candidate_state()
    before = support.state_binding(state)
    selected = support.select_support(state.rows,owned_names)
    inherited = support.parent_seed_paths()
    result = closure.assemble_bottom_layer_bundle(selected.frontier,
        seed_bundles=(*(() if seed_only else inherited),*seed_bundles),batch_size=1,
        report=lambda message:print(message,flush=True))
    authoring_rss_bytes()
    payload = closure.encode_proof_bundle(result.bundle,result.target).encode('utf-8')
    if len(payload) > closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
        raise support.PolynomialDivisionError('actual proof data exceeds the unchanged bundle payload limit')
    final_state = support.load_candidate_state()
    if support.state_binding(final_state) != before:
        raise support.PolynomialDivisionError('the exact sources changed during genuine proof authoring')
    authoring_rss_bytes()
    destination.parent.mkdir(parents=True,exist_ok=True)
    authoring_rss_bytes()
    with destination.open('xb') as stream:
        stream.write(payload)
    peak = authoring_rss_bytes()
    return {'artifact':str(destination),'bytes':len(payload),'sha256':sha256(payload).hexdigest(),
        'original_ha_checked':True,'nodes':result.receipt.node_count,
        'edges':result.receipt.dependency_edges,'body_nodes':result.receipt.total_body_nodes,
        'owned_rows':len(selected.owned),'inherited_alpha_v31_rows':len(selected.parent_support),
        'cross_track_rows':len(selected.current_support),'peak_rss_bytes':peak,
        'draft_proof_data_only':True,'independent_lean_checked':False,
        'final_complete_inventory_acceptance':False,'alpha_admission_performed':False,
        'stable_admission_performed':False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--through',type=int,help='nonempty source-order prefix of the complete draft rows')
    parser.add_argument('--module',choices=[item.module for item in support.FACTORIES])
    parser.add_argument('--seed',type=Path,action='append',default=[])
    parser.add_argument('--seed-only',action='store_true')
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU,CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    state = support.load_candidate_state()
    if args.module:
        first = 0
        for owner in support.FACTORIES:
            if owner.module == args.module:
                selected = state.rows[first:first+owner.count]
                break
            first += owner.count
    else:
        selected = state.rows
    if args.through is not None:
        if not 0 < args.through <= len(selected):
            parser.error('--through requires a nonempty in-range authoring prefix')
        selected = selected[:args.through]
    report = export_authoring_bundle(tuple(row.name for row in selected),args.output,
                                     seed_bundles=tuple(args.seed),seed_only=args.seed_only)
    print(support.canonical(report).decode(),flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
