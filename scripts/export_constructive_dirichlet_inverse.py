#!/usr/bin/env python3
"""Author actual non-admitting Dirichlet-inverse proof data in one bound.

All sixteen inherited seed identities remain authenticated, including the
local 113-row generation. Every supplied seed body and the resulting complete
cone reach the original HA checker. Staging prefixes are proof data only;
whole-tranche exact novelty, independent Lean and ordinary-root checks remain
separate mandatory acceptance gates. No prior success receipt is an input.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from importlib import import_module
from pathlib import Path
import resource
import signal

from check_constructive_bottom_layers import authoring_rss_bytes
from constructive_dirichlet_inverse_support import previous_seed_paths, select_support
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec


AUTHORING_GROUPS = (
    ("dirichlet-signed-units", ("dirichlet_signed_unit_candidate",)),
    ("dirichlet-triangular", ("dirichlet_triangular_candidate",)),
    ("dirichlet-inverses", ("dirichlet_inverse_candidate",)),
)
CPU_LIMITS = (170, 175)
WALL_SECONDS = 180


def module_rows(module):
    return getattr(import_module("peano_lab.library." + module),
                   "make_" + module + "_theorems")(TheoremSpec)


def authoring_rows():
    """Current ordinary authoring syntax, without freezing prospective counts."""
    return tuple(row for _, modules in AUTHORING_GROUPS for module in modules for row in module_rows(module))


def export_authoring_bundle(new_rows, owned_names, output, *, seed_bundles=(), seed_only=False):
    """Reuse original proof construction, with an RSS gate before any write.

    The CLI installs the original CPU/wall limits; programmatic callers must
    use the same bounded authoring window. The returned receipt comes solely
    from the unchanged whole-bundle HA checker, not a synthetic projection.
    """
    destination = Path(output)
    if destination.exists() or destination.is_symlink():
        raise closure.BottomLayerClosureError("refusing to overwrite an existing mathematical artifact")
    if type(seed_only) is not bool or type(seed_bundles) is not tuple:
        raise closure.BottomLayerClosureError("seed options require an explicit Boolean and exact tuple")
    if seed_only and not seed_bundles:
        raise closure.BottomLayerClosureError("seed-only authoring requires actual explicit proof data")
    # A small complete seed can avoid reconstructing unrelated old bodies,
    # but it never skips source/spec/pin authentication of the four parents.
    historical = previous_seed_paths()
    selected = select_support(new_rows, owned_names)
    result = closure.assemble_bottom_layer_bundle(
        selected.frontier, seed_bundles=(*(() if seed_only else historical), *seed_bundles),
        batch_size=1, report=lambda message: print(message, flush=True),
    )
    authoring_rss_bytes()
    payload = closure.encode_proof_bundle(result.bundle, result.target).encode("utf-8")
    if len(payload) > closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
        raise closure.BottomLayerClosureError("the actual proof artifact exceeds the unchanged bundle size bound")
    authoring_rss_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    authoring_rss_bytes()
    with destination.open("xb") as stream:
        stream.write(payload)
    peak = authoring_rss_bytes()
    print(f"NON-ADMITTING bottom-layer original-kernel ACCEPT: nodes={result.receipt.node_count}; "
          f"edges={result.receipt.dependency_edges}; body-nodes={result.receipt.total_body_nodes}; "
          f"bytes={len(payload)}; sha256={sha256(payload).hexdigest()}", flush=True)
    return selected, result, peak


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=[slug for slug, _ in AUTHORING_GROUPS], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=Path, action="append", default=[])
    parser.add_argument("--through", type=int, help="author only a nonempty family prefix as checked staging data")
    parser.add_argument("--seed-only", action="store_true", help="use only explicit actual seeds, with every reused body rechecked")
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    if args.output.exists() or args.output.is_symlink():
        parser.error("refusing to overwrite an existing mathematical artifact")
    if args.seed_only and not args.seed:
        parser.error("--seed-only requires actual explicit proof data")
    owned = tuple(row.name for module in dict(AUTHORING_GROUPS)[args.family] for row in module_rows(module))
    if args.through is not None:
        if not 0 < args.through <= len(owned):
            parser.error("--through must select a nonempty in-range family prefix")
        owned = owned[:args.through]
    selected, result, peak = export_authoring_bundle(
        authoring_rows(), owned, args.output, seed_bundles=tuple(args.seed), seed_only=args.seed_only,
    )
    print(f"Exported {len(selected.owned)} authored owned rows; {result.receipt.node_count} actual checked nodes including packaging.")
    print(f"Original HA only; exact 3756-prior-row novelty and independent Lean remain mandatory separate gates; peak RSS {peak} bytes.")
    print("No complete-tranche, Alpha/Stable, commit or publication claim is made by this authoring command.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
