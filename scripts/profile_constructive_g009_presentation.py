#!/usr/bin/env python3
"""Read-only G009 presentation-cost measurements, never proof acceptance.

Run only after the genuine final artifact, source pins and actual v31 atlas
are registered.  This diagnostic does not run proof workers, synthesize an
audit, build a corpus, render pages, invoke publication, or write files.
It measures the real ninety statement/script compactions and decoded body
metrics, then releases every decoded certificate reference before loading
the actual catalogue and conservative definition DAG.

The renderer normally inherits its support selection from the real audit.
This separate profile does not rebuild that full selection: exact source
target ASTs locate the owned bodies in the literally pinned final bundle.
Consequently this measures the requested presentation operations, not the
complete fresh-audit/UI pipeline or the memory occupied by rendered HTML.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import gc
from hashlib import sha256
import json
from pathlib import Path
import resource
import signal
import sys
import time


# Imports of the genuine production modules must not create bytecode files.
sys.dont_write_bytecode = True

CPU_LIMITS = (170, 175)
WALL_SECONDS = 180
MAX_RSS_BYTES = 1536 * 1024 * 1024
SCHEMA = 'peano-g009-presentation-cost-diagnostic-v1'


class ProfileError(RuntimeError):
    """A literal-input or diagnostic resource boundary failed closed."""


def _peak_rss_bytes():
    factor = 1 if sys.platform == 'darwin' else 1024
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * factor
    if type(peak) is not int or not 0 < peak <= MAX_RSS_BYTES:
        raise ProfileError('presentation profile exceeded the original 1536MiB RSS bound')
    return peak


def _emit(value):
    print(json.dumps(value, ensure_ascii=False, allow_nan=False,
                     sort_keys=True, separators=(',', ':')), flush=True)


def _measurement(name, started, started_cpu, **counts):
    result = {
        'phase': name,
        'elapsed_seconds': time.monotonic() - started,
        'cpu_seconds': time.process_time() - started_cpu,
        'peak_rss_bytes': _peak_rss_bytes(),
        **counts,
    }
    _emit({'schema': SCHEMA, 'diagnostic_only': True, 'measurement': result})
    return result


def _compact_owned_rows(reader, state, bundle):
    """Return strings/counts only; no decoded proof escapes this frame."""
    definitions = reader.definition_closure(tuple(dict.fromkeys((
        *(definition.name for definition in reader.ALL_BERTRAND_DEFINITIONS),
        *reader.EXTRA_DEFINITIONS,
        *(definition.name for definition in reader.G009_DEFINITIONS),
    ))))
    compactor = reader._FormulaCompactor(definitions)
    candidates = defaultdict(list)
    for node in bundle.nodes:
        candidates[hash(node.target)].append(node.node_id)
    nodes_by_id = {node.node_id: node for node in bundle.nodes}
    if len(nodes_by_id) != len(bundle.nodes):
        raise ProfileError('the actual final bundle repeats a node identity')
    readings, metrics = [], []
    for row in state.rows:
        formula = reader.closure._closed_formula(row.statement)
        matches = [index for index in candidates.get(hash(formula), ())
                   if nodes_by_id[index].target == formula]
        if len(matches) != 1 or matches[0] == bundle.root:
            raise ProfileError('an exact source theorem has no unique literal bundle target: ' + row.name)
        started, started_cpu = time.monotonic(), time.process_time()
        reading = compactor.compact(row.statement)
        reader.model._compact_script(row, compactor, reading)
        body_nodes, body_depth = reader.proof_metrics(nodes_by_id[matches[0]].body)
        if (type(body_nodes) is not int or body_nodes <= 0
                or type(body_depth) is not int or body_depth <= 0):
            raise ProfileError('the decoded actual body has invalid structural metrics')
        readings.append(reading)
        metrics.append({'name': row.name, 'node_id': matches[0],
                        'body_nodes': body_nodes, 'body_depth': body_depth,
                        'elapsed_seconds': time.monotonic() - started,
                        'cpu_seconds': time.process_time() - started_cpu})
        _peak_rss_bytes()
    if len(readings) != 90 or len({item['node_id'] for item in metrics}) != 90:
        raise ProfileError('the diagnostic did not visit exactly ninety distinct owned bodies')
    used = {identifier for reading in readings for identifier in reading['definition_uses']}
    wanted = {item.name for item in reader.G009_DEFINITIONS} | set(reader.EXTRA_DEFINITIONS)
    displayed = reader.definition_closure(tuple(item.name for item in definitions
                                                if item.stable_id in used or item.name in wanted))
    records = reader._definition_records(displayed)
    return readings, metrics, records


def profile():
    """Fixed real inputs only; return diagnostic measurements, not a receipt."""
    measurements = []
    started, started_cpu = time.monotonic(), time.process_time()
    import build_constructive_g009_explorer as reader

    expected_reader = Path(__file__).resolve().with_name('build_constructive_g009_explorer.py')
    if (Path(reader.__file__).resolve() != expected_reader
            or reader.HERE != reader.ROOT/'scripts' or reader.IN_REPOSITORY is not True):
        raise ProfileError('the profile requires its exact production sibling reader')
    if (reader.proof_audit.CPU_LIMITS != CPU_LIMITS
            or reader.proof_audit.WALL_SECONDS != WALL_SECONDS
            or reader.proof_audit.MAX_RSS_BYTES != MAX_RSS_BYTES):
        raise ProfileError('the diagnostic and actual worker resource contracts differ')
    pin = reader.checkpoints.require_final_inventory()
    # This requires the genuine final source/artifact registration, actual
    # published v31 atlas, all catalogue components and immutable assets.
    # It checks identities only; no saved receipt or proof authority is read.
    binding = reader._render_binding()
    measurements.append(_measurement('literal_input_preflight', started, started_cpu))

    started, started_cpu = time.monotonic(), time.process_time()
    state = reader.support.load_candidate_state(final=True)
    if (len(state.rows) != 90 or len({row.name for row in state.rows}) != 90
            or state.sources != reader.support.MATH_SOURCE_PINS
            or state.specs_sha256 != reader.support.NEW_SPECS_SHA256):
        raise ProfileError('the final ninety-row source inventory changed')
    payload = reader.support.bounded_bytes(reader.ROOT / pin.path, pin.bytes)
    if len(payload) != pin.bytes or sha256(payload).hexdigest() != pin.sha256:
        raise ProfileError('the final literal artifact changed before diagnostic decoding')
    bundle, target = reader.decode_proof_bundle(payload.decode('utf-8'))
    if (len(bundle.nodes) != pin.nodes or pin.nodes != 462
            or bundle.root != 461 or bundle.nodes[-1].node_id != bundle.root
            or bundle.nodes[-1].target != target):
        raise ProfileError('the actual final 461-theorem plus packaging inventory changed')
    measurements.append(_measurement('actual_sources_and_bundle_decode', started, started_cpu,
                                     source_theorems=90, literal_bundle_nodes=pin.nodes,
                                     literal_bundle_bytes=pin.bytes))

    started, started_cpu = time.monotonic(), time.process_time()
    readings, metrics, definition_records = _compact_owned_rows(reader, state, bundle)
    measurements.append(_measurement('exact_owned_compaction_and_actual_body_metrics', started, started_cpu,
                                     source_theorems=len(readings),
                                     script_commands=sum(len(row.script) for row in state.rows),
                                     owned_body_nodes=sum(item['body_nodes'] for item in metrics),
                                     max_owned_body_depth=max(item['body_depth'] for item in metrics),
                                     reader_definition_records=len(definition_records)))

    started, started_cpu = time.monotonic(), time.process_time()
    # _compact_owned_rows returned no node/body/formula object.  Its frame,
    # candidate map and matches are gone.  Retain the actual literal payload,
    # source strings and reading dictionaries as the real renderer does;
    # release the decoded certificate graph before the catalogue allocation.
    del bundle, target
    gc.collect()
    measurements.append(_measurement('release_decoded_certificates_before_catalogue', started, started_cpu))

    started, started_cpu = time.monotonic(), time.process_time()
    atlas = reader._atlas()
    parent_files = atlas.parent_files()
    campaign = json.loads(parent_files['campaign.json'])
    catalog = atlas.load_catalog(reader.ROOT / atlas.CATALOG_PATH,
                                 expected_sha256=atlas.CATALOG_SHA256)
    if (type(catalog) is not dict or type(catalog.get('theorems')) is not list
            or len(catalog['theorems']) != 3796):
        raise ProfileError('the actual logical Alpha v31 catalogue inventory changed')
    measurements.append(_measurement('actual_logical_v31_catalogue', started, started_cpu,
                                     logical_catalogue_theorems=len(catalog['theorems'])))

    started, started_cpu = time.monotonic(), time.process_time()
    # Add only literal conservative definition records to this private JSON
    # object.  The actual parent's G009 goal, status and proof claims remain
    # untouched; no current research audit or "proved" record is fabricated.
    for definition in reader.G009_DEFINITIONS:
        if definition.name in campaign['definitions']:
            raise ProfileError('a new conservative definition collides with the actual parent')
        campaign['definitions'][definition.name] = atlas._definition_record(definition)
    graph = atlas.build_definition_graph(campaign)
    if (graph.get('reviewed_definition_count') != 383
            or graph.get('reviewed_definition_edge_count') != 825):
        raise ProfileError('the actual additive 383-definition/825-edge registry changed')
    measurements.append(_measurement('actual_conservative_definition_dag', started, started_cpu,
                                     new_definition_records=len(reader.G009_DEFINITIONS),
                                     reviewed_definitions=graph['reviewed_definition_count'],
                                     reviewed_definition_edges=graph['reviewed_definition_edge_count']))

    started, started_cpu = time.monotonic(), time.process_time()
    if atlas.parent_files() != parent_files or reader._render_binding() != binding:
        raise ProfileError('literal presentation inputs changed during the diagnostic')
    measurements.append(_measurement('final_literal_input_recheck', started, started_cpu))
    return {'schema': SCHEMA, 'diagnostic_only': True,
            'proof_workers_executed': 0, 'proof_acceptance': False,
            'snapshot_files_written': 0, 'publication_performed': False,
            'measurement_scope': 'exact-owned-compaction/body-metrics/catalogue/definition-DAG; no HTML or proof audit',
            'render_source_binding_sha256': binding,
            'literal_bundle_sha256': pin.sha256,
            'source_specs_sha256': state.specs_sha256,
            'limits': {'cpu_seconds': list(CPU_LIMITS), 'wall_seconds': WALL_SECONDS,
                       'max_rss_bytes': MAX_RSS_BYTES},
            'measurements': measurements,
            'slowest_owned_compactions': sorted(metrics, key=lambda item: item['cpu_seconds'], reverse=True)[:10],
            'peak_rss_bytes': _peak_rss_bytes()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)  # No path, receipt, subset, output or limit override.
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    started, started_cpu = time.monotonic(), time.process_time()
    try:
        result = profile()
        result['elapsed_seconds'] = time.monotonic() - started
        result['cpu_seconds'] = time.process_time() - started_cpu
        result['peak_rss_bytes'] = _peak_rss_bytes()
        if result['elapsed_seconds'] >= WALL_SECONDS:
            raise ProfileError('the original 180-second diagnostic wall bound expired')
        _emit(result)
        return 0
    except Exception as error:
        _emit({'schema': SCHEMA, 'diagnostic_only': True, 'measurement_complete': False,
               'error_type': type(error).__name__, 'error': str(error),
               'proof_acceptance': False, 'snapshot_files_written': 0})
        return 1
    finally:
        signal.alarm(0)


if __name__ == '__main__':
    raise SystemExit(main())
