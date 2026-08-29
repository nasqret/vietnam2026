#!/usr/bin/env python3
"""Author complete non-admitting Dirichlet/Möbius dependency bundles.

This writes actual original-HA proof data, never a Lean/admission receipt.
Every selected inherited body is rechecked; earlier source and artifact bytes
are authenticated by the immutable three-generation support adapter. Exact
whole-tranche novelty is a separate mandatory fresh audit job, not duplicated
inside each proof-construction window. Partial prefixes are only proof-data
seeds and cannot be registered as complete campaign checkpoints.
"""

from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path
import resource
import signal

from constructive_dirichlet_support import previous_seed_paths,select_support
from check_constructive_bottom_layers import authoring_rss_bytes
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec


AUTHORING_GROUPS=(
    ('finite-support',('signed_finite_support_candidate',)),
    ('dirichlet-convolution',('dirichlet_convolution_candidate','dirichlet_commutativity_candidate')),
    ('dirichlet-fubini',('dirichlet_fubini_candidate','dirichlet_associativity_candidate')),
    ('dirichlet-units',('dirichlet_units_candidate',)),
    ('mobius-inversion',('mobius_inversion_candidate',)),
)


def module_rows(module):
    return getattr(import_module('peano_lab.library.'+module),'make_'+module+'_theorems')(TheoremSpec)


def authoring_rows():
    return tuple(row for _,modules in AUTHORING_GROUPS for module in modules for row in module_rows(module))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family',choices=[slug for slug,_ in AUTHORING_GROUPS],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=Path,action='append',default=[])
    parser.add_argument('--through',type=int,help='author only the first N family rows as checked staging data')
    parser.add_argument('--seed-only',action='store_true',help='use only explicit seeds; every reused body is still actually HA checked')
    args=parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)
    if args.output.exists() or args.output.is_symlink():
        parser.error('refusing to overwrite an existing mathematical artifact')
    owned=tuple(row.name for module in dict(AUTHORING_GROUPS)[args.family] for row in module_rows(module))
    if args.through is not None:
        if not 0<args.through<=len(owned):parser.error('--through must select a nonempty in-range family prefix')
        owned=owned[:args.through]
    if args.seed_only and not args.seed:parser.error('--seed-only requires actual explicit proof data')
    # Authentication is retained even when a smaller already-checked seed
    # covers the entire requested cone. Closure still rechecks every reused
    # body and then the complete resulting bundle with the original kernel.
    historical=previous_seed_paths()
    selected=select_support(authoring_rows(),owned)
    result=closure.export_bottom_layer_bundle(selected.frontier,args.output,
        seed_bundles=(*(() if args.seed_only else historical),*args.seed),batch_size=1)
    peak=authoring_rss_bytes()
    print(f'Exported {len(selected.owned)} authored owned rows; {result.receipt.node_count} actual checked nodes including packaging.')
    print(f'Original HA only; exact novelty and independent Lean remain mandatory separate gates; peak RSS {peak} bytes.')
    print('No complete-tranche, Alpha/Stable, commit or publication claim is made by this authoring command.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
