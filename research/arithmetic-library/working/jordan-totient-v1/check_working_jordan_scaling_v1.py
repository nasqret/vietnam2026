"""One additive Jordan107 author/HA+Lean/ordinary-root closure runner.

Reuses the frozen Jordan96 output safety and unchanged actual-source bundle
assembler. Each command has one original resource window. No observation is
proof authority and no candidate or local definition is admitted to Alpha.
"""
import argparse
from dataclasses import asdict
from hashlib import sha256
import importlib
import os
from pathlib import Path
import re
import resource
import signal
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(ROOT / 'peano-lab/py'), str(ROOT / 'scripts')]
import check_working_jordan_extension_v1 as prior

support, require = prior.support, prior.require
write_new, new_destination, basename = prior.write_new, prior.new_destination, prior.basename
SEED = support.FilePin(
    'research/arithmetic-library/working/jordan-totient-v1/artifacts/working-jordan-prime-power-unit-prefix-96-proof-bundle-v1.json',
    1620004, '9164d35758d1fa15d18ec792a429cbb33fd4c511df5651b9f15d37bececf5ea7')
PRIOR_BINDING = '42a633abc05b777fd4c882e6057ef4fef7a8b3c5b56a86505eef28dc1f06d787'
CONTROLS = ('jordan_tuple_scaling_candidate.py', 'test_jordan_tuple_scaling_candidate.py',
    'jordan_scaling_definition_dag.py', 'test_jordan_scaling_definitions.py',
    'check_working_jordan_scaling_v1.py',
    '../jordan-orders-fields-v1/existence_definition_dag.py')
NEW_NAMES = (
    'jordan_scale_coordinate_strict_bound', 'jordan_scale_coordinate_strict_bound_reflect',
    'jordan_tuple_scaling_exists', 'jordan_tuple_scaling_all_divisible',
    'jordan_tuple_scaling_respects_tuple_equality', 'jordan_tuple_scaling_injective',
    'jordan_tuple_all_divisible_quotient_exists', 'jordan_tuple_scaling_preserves_box_bound',
    'jordan_tuple_scaling_reflects_box_bound', 'jordan_box_scaling_divisible_image_exists',
    'jordan_box_divisible_scaling_preimage_exists')
PRINCIPALS = (NEW_NAMES[4], NEW_NAMES[5], NEW_NAMES[9], NEW_NAMES[10])


def source_binding():
    inherited = prior.source_binding()[0]
    require(inherited == PRIOR_BINDING, 'frozen Jordan96 source binding changed')
    local = [asdict(support.actual_pin((HERE / name).resolve())) for name in CONTROLS]
    return sha256(support.canonical(dict(prior96=inherited, local=local))).hexdigest(), local


def selection():
    from peano_lab.library import campaign_bottom_layer_closure as closure
    from peano_lab.library.theorems import TheoremSpec, _closed_formula
    _, old_frontier, old_plan = prior.selection()
    module = importlib.import_module('jordan_tuple_scaling_candidate')
    require(Path(module.__file__).resolve() == HERE / 'jordan_tuple_scaling_candidate.py', 'foreign scaling source')
    new = module.make_jordan_tuple_scaling_candidate_theorems(TheoremSpec)
    require(type(new) is tuple and tuple(row.name for row in new) == NEW_NAMES, 'exact new11 inventory changed')
    known = {row.name: row for row in (*closure.parent_snapshot().specs, *old_frontier)}
    pool = dict(known)
    for name in ('finite_pointwise_mul_recode_candidate', 'finite_division_prefix_candidate'):
        provider = importlib.import_module('peano_lab.library.' + name)
        for row in getattr(provider, 'make_' + name + '_theorems')(TheoremSpec):
            if row.name in pool:
                require(_closed_formula(pool[row.name].statement) == _closed_formula(row.statement)
                        and pool[row.name].dependencies == row.dependencies, 'original provider contract changed')
            else:
                pool[row.name] = row
    for row in new:
        require(row.name not in pool, 'new theorem shadows an old source')
        pool[row.name] = row
    ordered, active = {}, set()
    def visit(name):
        if name in known or name in ordered:
            return
        require(name in pool and name not in active, 'missing or cyclic actual scaling prerequisite: ' + name)
        active.add(name)
        for dependency in pool[name].dependencies:
            visit(dependency)
        active.remove(name)
        ordered[name] = pool[name]
    for row in new:
        visit(row.name)
    frontier = old_frontier + tuple(ordered.values())
    plan = closure.bottom_layer_plan(frontier)
    current = {row.name: row for row in plan.rows}
    require(all(row.name in current and current[row.name].dependencies == row.dependencies
                and current[row.name].statement_sha256 == row.statement_sha256
                for row in old_plan.rows), 'the complete old96 source cone changed')
    visited = set()
    def ancestors(name):
        if name in visited:
            return
        visited.add(name)
        for dependency in current[name].dependencies:
            ancestors(dependency)
    for name in PRINCIPALS:
        ancestors(name)
    require(set(NEW_NAMES) <= visited, 'four ordinary roots do not cover all new11 theorems')
    return new, frontier, plan


def lean_check(frontier, plan, path, payload, count, root):
    from peano_lab.library import campaign_bottom_layer_closure as closure
    import constructive_bottom_layer_checkpoints as independent
    checkpoint = independent.Checkpoint('working-jordan-scaling-107', (),
        path.relative_to(ROOT).as_posix(), len(payload), sha256(payload).hexdigest(),
        len(frontier), tuple(plan.root_names), '', closure._specs_digest(frontier))
    independent._lean_check(checkpoint, count, root, payload)


def run(args):
    started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    from check_constructive_bottom_layers import authoring_rss_bytes
    stop = threading.Event()
    def resources():
        require(resource.getrlimit(resource.RLIMIT_CPU) == (170, 175)
                and time.monotonic() - started < 180, 'original resource window changed or expired')
        return authoring_rss_bytes()
    def monitor():
        while not stop.wait(.1):
            try:
                authoring_rss_bytes()
            except RuntimeError:
                os._exit(137)
    threading.Thread(target=monitor, daemon=True).start()
    require((args.task == 'root') == (args.name is not None), 'ordinary root/task mismatch')
    require(args.name is None or args.name in PRINCIPALS, 'not an exact maximal new root')
    require((args.task != 'author') == (args.source_binding is not None), 'verification needs exact source binding')
    require(args.task == 'root' or args.ordinary_name is None, 'ordinary destination is root-only')
    if args.task == 'author':
        require(args.artifact_bytes is None and args.artifact_sha256 is None, 'author cannot consume an artifact identity')
    else:
        require(args.artifact_bytes is not None and args.artifact_sha256 is not None, 'missing exact artifact identity')
    require(re.fullmatch(r'working-jordan-scaling-prefix-107-proof-bundle-v[1-9][0-9]*\.json', args.artifact_name),
            'not a new versioned Jordan107 artifact')
    path = HERE / 'artifacts' / args.artifact_name
    record = new_destination(HERE / 'observations' / basename(args.record_name))
    inputs = new_destination(HERE / 'observations' / basename(args.record_name[:-5] + '-inputs.json'))
    output = new_destination(path) if args.task == 'author' else None
    if args.task == 'root':
        prefix = 'working-jordan-107-ordinary-' + str(NEW_NAMES.index(args.name) + 1)
        filename = args.ordinary_name or prefix + '-proof-bundle-v1.json'
        require(re.fullmatch(prefix + r'-proof-bundle-v[1-9][0-9]*\.json', filename), 'ordinary artifact/root mismatch')
        output = new_destination(HERE / 'artifacts' / basename(filename))
    binding, local = source_binding()
    require(args.source_binding is None or args.source_binding == binding, 'source binding differs from authoring')
    support.read_pin(SEED)
    payload = prior.exact_payload(path, args.artifact_bytes, args.artifact_sha256) if args.task != 'author' else None
    snapshot = dict(schema='working-jordan-scaling-inputs-v1', task=args.task, root=args.name,
        source_binding=binding, prior96_binding=PRIOR_BINDING, local_source_pins=local, seed=asdict(SEED),
        artifact=None if payload is None else asdict(support.actual_pin(path)), proof_authority=False,
        cpu_limits=[170, 175], wall_alarm_seconds=180, rss_limit_bytes=1536 * 1024 * 1024, proof_depth_limit=256)
    input_pin = write_new(inputs, support.canonical(snapshot) + b'\n')
    report = dict(schema='working-jordan-scaling-check-v1', task=args.task, root=args.name,
        source_binding=binding, input_snapshot=input_pin, proof_authority=False,
        alpha_admitted=False, stable_changed=False, original_ha_checked=False,
        independent_same_byte_lean_checked=False, ordinary_empty_context_checked=False,
        passed=False, error=None, cpu_limits=[170, 175], wall_alarm_seconds=180,
        rss_limit_bytes=1536 * 1024 * 1024, proof_depth_limit=256)
    try:
        from peano_lab.library import campaign_bottom_layer_closure as closure
        from peano_lab.library.proof_bundle import (
            BundleNode, ProofBundle, decode_proof_bundle, encode_proof_bundle, check_proof_bundle)
        from peano_lab.library.theorems import _closed_formula
        from peano_lab.kernel.checker import check
        import jordan_scaling_definition_dag as definitions
        require(len(definitions.PREVIOUS) == 493 and len(definitions.ALL_DEFINITIONS) == 494,
                'append-only local notation inventory changed')
        catalog = support.FilePin(closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES, closure.PARENT_CATALOG_SHA256)
        support.read_pin(catalog)
        new, frontier, plan = selection()
        parents = closure.validate_parent_provider_bytes()
        report.update(owned_count=107, new_names=NEW_NAMES, ordinary_root_names=PRINCIPALS, plan=asdict(plan),
            frontier_specs_sha256=closure._specs_digest(frontier), original_parent_catalog=asdict(catalog),
            original_parent_documents=[asdict(p) for p in parents],
            local_definition_count=494, local_new_definition_ids=['ND0440'])
        if args.task == 'author':
            result = closure.assemble_bottom_layer_bundle(frontier, seed_bundles=(ROOT / SEED.path,), batch_size=1,
                report=lambda message: print(message, flush=True))
            require(result.plan == plan, 'actual assembler plan differs')
            payload = encode_proof_bundle(result.bundle, result.target).encode()
            report.update(original_ha_checked=True, receipt=asdict(result.receipt), body_origins=result.origins)
        else:
            bundle, target = decode_proof_bundle(payload.decode())
            if args.task == 'bundle':
                receipt = closure.check_bottom_layer_bundle(frontier, bundle, target)
                lean_check(frontier, plan, path, payload, receipt.node_count, bundle.root)
                report.update(original_ha_checked=True, independent_same_byte_lean_checked=True, receipt=asdict(receipt))
            else:
                exact = next(row for row in new if row.name == args.name)
                proof = closure.replay_bottom_layer_theorem(frontier, args.name, bundle, target)
                formula = _closed_formula(exact.statement)
                require(proof.spec == exact and proof.formula == formula and check((), proof.certificate, formula),
                        'original empty-context root rejected')
                standalone = ProofBundle((BundleNode(0, formula, (), proof.certificate),), 0)
                payload = encode_proof_bundle(standalone, formula).encode()
                actual, goal = decode_proof_bundle(payload.decode())
                receipt = check_proof_bundle(actual, goal)
                require(goal == formula and len(actual.nodes) == 1 and actual.nodes[0].dependencies == (),
                        'ordinary serialization changed the exact theorem')
                lean_check(frontier, plan, output, payload, 1, 0)
                report.update(original_ha_checked=True, independent_same_byte_lean_checked=True,
                    ordinary_empty_context_checked=True, ordinary_proof_nodes=proof.proof_nodes,
                    standalone_receipt=asdict(receipt))
        support.read_pin(SEED)
        if args.task != 'author':
            prior.exact_payload(path, args.artifact_bytes, args.artifact_sha256)
        require(closure.validate_parent_provider_bytes() == parents, 'original proof providers changed')
        support.read_pin(catalog)
        require(source_binding()[0] == binding, 'bound source changed during execution')
        require(not any(name.startswith('peano_lab.library.editions') for name in sys.modules), 'an edition was initialized')
        resources()
        report['artifact'] = write_new(output, payload) if output is not None else asdict(support.actual_pin(path))
        report['passed'] = True
    except Exception as error:
        report['error'] = dict(type=type(error).__name__, message=str(error)[:6000])
    report.update(seconds=time.monotonic() - started, peak_rss_bytes=resources())
    saved = write_new(record, support.canonical(report) + b'\n')
    require(source_binding()[0] == binding, 'bound source changed while saving observation')
    resources()
    stop.set()
    print(support.canonical(dict(record=saved, passed=report['passed'], error=report['error'],
        source_binding=binding, artifact=report.get('artifact'), seconds=report['seconds'],
        original_ha_checked=report['original_ha_checked'],
        independent_same_byte_lean_checked=report['independent_same_byte_lean_checked'],
        ordinary_empty_context_checked=report['ordinary_empty_context_checked'])).decode(), flush=True)
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', choices=('author', 'bundle', 'root'), required=True)
    parser.add_argument('--record-name', required=True)
    parser.add_argument('--artifact-name', default='working-jordan-scaling-prefix-107-proof-bundle-v1.json')
    parser.add_argument('--artifact-bytes', type=int)
    parser.add_argument('--artifact-sha256')
    parser.add_argument('--source-binding')
    parser.add_argument('--name', choices=PRINCIPALS)
    parser.add_argument('--ordinary-name')
    return run(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
