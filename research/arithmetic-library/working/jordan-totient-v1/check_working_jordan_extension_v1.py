"""Original HA, same-byte Lean and ordinary roots for ten additive Jordan lemmas.

One process performs one author/bundle/root task under the existing limits.
The actual Jordan86 bundle supplies previous proofs; the unchanged generic
assembler resolves actual original parent providers. Records identify inputs
and observations and never serve as theorem proofs or library admission.
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
import stat
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(ROOT / 'peano-lab/py'), str(ROOT / 'scripts')]
import working_jordan_count_support as support

require = support.require
MAX_BYTES = 64_000_000
CONTROLS = ('jordan_unit_modulus_candidate.py', 'test_jordan_unit_modulus_candidate.py',
    'jordan_prime_power_characterization_candidate.py',
    'test_jordan_prime_power_characterization_candidate.py',
    'test_jordan_extension_definitions.py',
    'check_working_jordan_extension_v1.py')
NEW_NAMES = (
    'jordan_tuple_bounded_one_entry_zero', 'jordan_zero_tuple_bounded_one',
    'jordan_tuples_bounded_one_equal', 'jordan_unit_modulus_singleton_enumeration',
    'jordan_totient_at_one', 'jordan_totient_at_one_unique',
    'jordan_primitive_tuple_avoids_prime_common_divisor',
    'jordan_prime_power_tuple_primitive_of_not_all_divisible',
    'jordan_prime_power_tuple_primitive_characterization',
    'jordan_prime_power_tuple_primitivity_invariant')
PRINCIPALS = (NEW_NAMES[5], NEW_NAMES[8], NEW_NAMES[9])
SEED = support.FilePin(
    'research/arithmetic-library/working/jordan-totient-v1/artifacts/working-jordan-count-prefix-86-proof-bundle-v1.json',
    1128894, '8eea457b6fa5164d2525a7b9c6a3966200de8a9f62fe926012f14f03caece95b')


def source_binding():
    prior = support.state_binding()
    local = [asdict(support.actual_pin(HERE / name)) for name in CONTROLS]
    return sha256(support.canonical(dict(prior86=prior, local=local))).hexdigest(), prior, local


def selection():
    from peano_lab.library import campaign_bottom_layer_closure as closure
    from peano_lab.library.theorems import TheoremSpec
    old, old_rows, frontier, old_plan = support.execution_selection(86)
    new = []
    for module_name, count in (('jordan_unit_modulus_candidate', 6),
                               ('jordan_prime_power_characterization_candidate', 4)):
        module = importlib.import_module(module_name)
        require(Path(module.__file__).resolve() == HERE / (module_name + '.py'),
                'foreign new theorem factory')
        rows = getattr(module, 'make_' + module_name + '_theorems')(TheoremSpec)
        require(type(rows) is tuple and len(rows) == count, 'new theorem count changed')
        new.extend(rows)
    require(len(old) == 86 and tuple(r.name for r in new) == NEW_NAMES,
            'the exact additive 86+10 inventory changed')
    frontier = frontier + tuple(new)
    plan = closure.bottom_layer_plan(frontier)
    current = {row.name: row for row in plan.rows}
    require(all(row.name in current and current[row.name].dependencies == row.dependencies
                and current[row.name].statement_sha256 == row.statement_sha256
                for row in old_plan.rows), 'the extension lost or changed a prior source theorem')
    return tuple(new), frontier, plan


def basename(value):
    require(type(value) is str and re.fullmatch(r'[a-z0-9][a-z0-9-]{0,150}\.json', value),
            'expected a local plain JSON basename')
    return value


def artifact_path(name):
    basename(name)
    require(re.fullmatch(r'working-jordan-prime-power-unit-prefix-96-proof-bundle-v[1-9][0-9]*\.json', name),
            'not a versioned exact Jordan96 extension artifact')
    return HERE / 'artifacts' / name


def new_destination(path):
    require(path.parent in (HERE / 'artifacts', HERE / 'observations'), 'nonlocal output')
    require(not path.exists() and not path.is_symlink(), 'immutable output already exists')
    for parent in path.parent.parents:
        require(stat.S_ISDIR(parent.lstat().st_mode), 'linked/non-directory output ancestor')
    if path.parent.exists() or path.parent.is_symlink():
        info = path.parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid(), 'unsafe output directory')
    return path


def write_new(path, payload):
    require(type(payload) is bytes and 0 < len(payload) <= MAX_BYTES, 'invalid bounded output')
    new_destination(path)
    path.parent.mkdir(exist_ok=True)
    ancestors = tuple((p, p.lstat().st_dev, p.lstat().st_ino, p.lstat().st_mode)
                      for p in (path.parent, *path.parent.parents))
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        opened = os.fstat(directory)
        require((opened.st_dev, opened.st_ino, opened.st_mode) == ancestors[0][1:]
                and opened.st_uid == os.getuid(), 'output directory changed')
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o600, dir_fd=directory)
        with os.fdopen(fd, 'wb') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
                    'unsafe output inode')
            require(stream.write(payload) == len(payload), 'short output write')
            stream.flush()
        require(all((p.lstat().st_dev, p.lstat().st_ino, p.lstat().st_mode) == (dev, ino, mode)
                    for p, dev, ino, mode in ancestors), 'output ancestor changed during write')
    finally:
        os.close(directory)
    require(support.raw(path) == payload, 'saved bytes differ')
    return asdict(support.actual_pin(path))


def exact_payload(path, size, digest):
    require(type(size) is int and 0 < size <= MAX_BYTES and type(digest) is str
            and re.fullmatch('[0-9a-f]{64}', digest), 'missing exact artifact bytes/SHA256')
    payload = support.raw(path, MAX_BYTES)
    require(len(payload) == size and sha256(payload).hexdigest() == digest, 'actual artifact bytes differ')
    return payload


def lean_check(frontier, plan, path, payload, count, root):
    from peano_lab.library import campaign_bottom_layer_closure as closure
    import constructive_bottom_layer_checkpoints as independent
    checkpoint = independent.Checkpoint('working-jordan-extension-96', (),
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
                and time.monotonic() - started < 180, 'original resource bound changed or expired')
        return authoring_rss_bytes()
    def monitor():
        while not stop.wait(.1):
            try:
                authoring_rss_bytes()
            except RuntimeError:
                os._exit(137)
    threading.Thread(target=monitor, daemon=True).start()
    require((args.task == 'root') == (args.name is not None), 'root/task mismatch')
    require(args.name is None or args.name in NEW_NAMES, 'not an exact new Jordan theorem')
    require(args.task == 'root' or args.ordinary_name is None, 'ordinary output is root-only')
    require((args.task != 'author') == (args.source_binding is not None), 'verification needs the exact source binding')
    if args.task == 'author':
        require(args.artifact_bytes is None and args.artifact_sha256 is None,
                'authoring cannot consume artifact identity arguments')
    else:
        require(args.artifact_bytes is not None and args.artifact_sha256 is not None,
                'verification needs exact artifact bytes and SHA256')
    path = artifact_path(args.artifact_name)
    record = new_destination(HERE / 'observations' / basename(args.record_name))
    inputs = new_destination(HERE / 'observations' / basename(args.record_name[:-5] + '-inputs.json'))
    output = None
    if args.task == 'author':
        output = new_destination(path)
    elif args.task == 'root':
        output = new_destination(HERE / 'artifacts' / basename(args.ordinary_name or (
            'working-jordan-96-ordinary-' + str(NEW_NAMES.index(args.name) + 1) + '-proof-bundle-v1.json')))
        require(re.fullmatch(r'working-jordan-96-ordinary-' + str(NEW_NAMES.index(args.name) + 1)
                            + r'-proof-bundle-v[1-9][0-9]*\.json', output.name), 'ordinary artifact/root mismatch')
    else:
        require(args.ordinary_name is None, 'ordinary output is root-only')
    binding, prior, local = source_binding()
    require(args.source_binding is None or args.source_binding == binding, 'source binding differs from authoring')
    support.read_pin(SEED)
    payload = exact_payload(path, args.artifact_bytes, args.artifact_sha256) if args.task != 'author' else None
    snapshot = dict(schema='working-jordan-extension-inputs-v1', task=args.task, root=args.name,
        source_binding=binding, prior86_binding=prior, local_source_pins=local, seed=asdict(SEED),
        artifact=None if payload is None else asdict(support.actual_pin(path)),
        cpu_limits=[170, 175], wall_alarm_seconds=180, rss_limit_bytes=1536 * 1024 * 1024,
        proof_depth_limit=256, proof_authority=False)
    input_pin = write_new(inputs, support.canonical(snapshot) + b'\n')
    report = dict(schema='working-jordan-extension-check-v1', task=args.task, root=args.name,
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
        catalog = support.FilePin(closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES,
                                  closure.PARENT_CATALOG_SHA256)
        support.read_pin(catalog)
        new, frontier, plan = selection()
        parents = closure.validate_parent_provider_bytes()
        report.update(owned_count=96, new_names=NEW_NAMES, plan=asdict(plan),
                      frontier_specs_sha256=closure._specs_digest(frontier),
                      original_parent_catalog=asdict(catalog),
                      original_parent_documents=[asdict(p) for p in parents])
        if args.task == 'author':
            result = closure.assemble_bottom_layer_bundle(frontier,
                seed_bundles=(ROOT / SEED.path,), batch_size=1,
                report=lambda message: print(message, flush=True))
            require(result.plan == plan, 'actual assembler plan differs')
            payload = encode_proof_bundle(result.bundle, result.target).encode()
            report.update(original_ha_checked=True, receipt=asdict(result.receipt),
                          body_origins=result.origins)
        else:
            bundle, target = decode_proof_bundle(payload.decode())
            if args.task == 'bundle':
                receipt = closure.check_bottom_layer_bundle(frontier, bundle, target)
                lean_check(frontier, plan, path, payload, receipt.node_count, bundle.root)
                report.update(original_ha_checked=True, independent_same_byte_lean_checked=True,
                              receipt=asdict(receipt))
            else:
                exact = next(row for row in new if row.name == args.name)
                proof = closure.replay_bottom_layer_theorem(frontier, args.name, bundle, target)
                formula = _closed_formula(exact.statement)
                require(proof.spec == exact and proof.formula == formula
                        and check((), proof.certificate, formula), 'original ordinary root rejected')
                standalone = ProofBundle((BundleNode(0, formula, (), proof.certificate),), 0)
                payload = encode_proof_bundle(standalone, formula).encode()
                actual, goal = decode_proof_bundle(payload.decode())
                receipt = check_proof_bundle(actual, goal)
                require(goal == formula and len(actual.nodes) == 1 and actual.nodes[0].dependencies == (),
                        'ordinary root serialization changed the theorem')
                lean_check(frontier, plan, output, payload, 1, 0)
                report.update(original_ha_checked=True, ordinary_empty_context_checked=True,
                    independent_same_byte_lean_checked=True, ordinary_proof_nodes=proof.proof_nodes,
                    standalone_receipt=asdict(receipt))
        support.read_pin(SEED)
        if args.task != 'author':
            exact_payload(path, args.artifact_bytes, args.artifact_sha256)
        require(closure.validate_parent_provider_bytes() == parents, 'original parent providers changed')
        support.read_pin(catalog)
        require(source_binding()[0] == binding, 'bound source changed during execution')
        require(not any(name.startswith('peano_lab.library.editions') for name in sys.modules),
                'an edition was initialized during non-admitting proof work')
        resources()
        if output is not None:
            report['artifact'] = write_new(output, payload)
        else:
            report['artifact'] = asdict(support.actual_pin(path))
        report['passed'] = True
    except Exception as error:
        report['error'] = dict(type=type(error).__name__, message=str(error))
    report.update(seconds=time.monotonic() - started, peak_rss_bytes=resources())
    saved = write_new(record, support.canonical(report) + b'\n')
    require(source_binding()[0] == binding, 'source changed while saving observation')
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
    parser.add_argument('--artifact-name', default='working-jordan-prime-power-unit-prefix-96-proof-bundle-v1.json')
    parser.add_argument('--artifact-bytes', type=int)
    parser.add_argument('--artifact-sha256')
    parser.add_argument('--source-binding')
    parser.add_argument('--name', choices=NEW_NAMES)
    parser.add_argument('--ordinary-name')
    return run(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
