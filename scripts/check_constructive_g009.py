#!/usr/bin/env python3
"""Fresh original-bounded final G009 verification; no receipt input mode.

One novelty worker, one complete HA/same-byte Lean worker and six separately
bounded ordinary principal workers. Literal source and artifact pins identify
the complete data; every acceptance still performs all eight fresh checks.
No partial authoring option is accepted here; export staging is a different
command and different API.
"""

from __future__ import annotations

import argparse
import gc
from hashlib import sha256
import os
from pathlib import Path
import re
import resource
import secrets
import signal
import sys

import constructive_g009_support as support
import constructive_g009_checkpoints as checkpoints
import check_constructive_lower_continuation as transport


SCRIPT = Path(__file__).resolve()
CPU_LIMITS = (170,175)
WALL_SECONDS = 180
PARENT_TIMEOUT_SECONDS = 185
MAX_RSS_BYTES = 1536*1024*1024
MAX_STDOUT_BYTES = 128*1024
MAX_STDERR_BYTES = 8*1024
SCHEMA = 'peano-g009-fresh-worker-v1'
CONTROLLER_WALL_SECONDS = (2+len(checkpoints.PRINCIPAL_ROOTS))*PARENT_TIMEOUT_SECONDS+WALL_SECONDS
# The existing strict decoder requires its exact newline-terminated encoding.
# Source-binding JSON has a separate byte convention and is not a wire codec.
canonical_message = transport._canonical

if (transport.ROOT != support.ROOT or any(getattr(transport,key) != globals()[key] for key in (
        'CPU_LIMITS','WALL_SECONDS','PARENT_TIMEOUT_SECONDS','MAX_RSS_BYTES','MAX_STDOUT_BYTES','MAX_STDERR_BYTES'))):
    raise RuntimeError('the unchanged bounded worker transport contract changed')


def binding():
    pin = checkpoints.require_final_inventory()
    state = support.load_candidate_state(final=True)
    independent = checkpoints.independent
    independent._check_lean_binary()
    return sha256(support.canonical({'sources':support.state_binding(state,final=True),
        'artifact':[pin.path,pin.bytes,pin.sha256,pin.nodes,pin.edges,pin.body_nodes],
        'principals':list(checkpoints.PRINCIPAL_ROOTS),
        'lean':[independent.LEAN_BINARY_BYTES,independent.LEAN_BINARY_SHA256]})).hexdigest()


def expected_novelty(state):
    return {'new_theorems':90,'prior_theorems':3796,'new_specs_sha256':state.specs_sha256,
            'exact_statement_ast_duplicates':[],'exact_ast_novelty_checked':True}


def validate_message(payload, *, kind, root, nonce, source_binding, expected):
    value = transport._decode_message(payload)
    if set(value) != {'schema','kind','slug','root','nonce','binding_sha256','limits','peak_rss_bytes','report'}:
        raise support.G009Error('the exact worker envelope fields changed')
    wanted = {'schema':SCHEMA,'kind':kind,'slug':checkpoints.SLUG,'root':root,'nonce':nonce,
              'binding_sha256':source_binding,'limits':{'cpu':list(CPU_LIMITS),
                  'wall_seconds':WALL_SECONDS,'max_rss_bytes':MAX_RSS_BYTES}}
    if canonical_message({key:value[key] for key in wanted}) != canonical_message(wanted):
        raise support.G009Error('stale, foreign, or incorrectly bounded worker response')
    peak = value['peak_rss_bytes']
    if type(peak) is not int or not 0 < peak <= MAX_RSS_BYTES:
        raise support.G009Error('worker exceeded the original observed RSS ceiling')
    transport._validate_report(value['report'],expected,family=kind == 'root')
    return value['report'],peak


def run_worker(kind,root,source_binding,expected):
    nonce = secrets.token_hex(32)
    command = [sys.executable,str(SCRIPT),'--worker',kind,'--nonce',nonce,'--binding',source_binding]
    if root is not None:
        command.extend(('--root',root))
    environment = os.environ.copy()
    environment.update(PYTHONPATH=os.pathsep.join((str(support.HERE),str(support.ROOT/'peano-lab/py'),
                                                 str(support.ROOT/'scripts'))),
                       PYTHONMALLOC='pymalloc',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
    print('Checking G009 '+kind+(' '+root if root else ''),file=sys.stderr,flush=True)
    # Existing exclusive-session/group cleanup and bounded pipe capture; no
    # old dispatcher, source binding, worker registry or successful receipt.
    payload = transport._capture_bounded(command,environment)
    return validate_message(payload,kind=kind,root=root,nonce=nonce,source_binding=source_binding,expected=expected)


def worker(kind,root,nonce,source_binding):
    resource.setrlimit(resource.RLIMIT_CPU,CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    if (re.fullmatch(r'[0-9a-f]{64}',nonce or '') is None
            or re.fullmatch(r'[0-9a-f]{64}',source_binding or '') is None):
        raise support.G009Error('invalid fresh-worker nonce or binding')
    if binding() != source_binding:
        raise support.G009Error('worker input differs from its live controller')
    # Release unreachable preflight temporaries before actual proof work.
    # This neither clears an old cache nor changes the binding or its checks.
    gc.collect()
    if kind == 'bundle' and root is None:
        report = checkpoints.verify_checkpoint()
    elif kind == 'root' and root in checkpoints.PRINCIPAL_ROOTS:
        report = checkpoints.verify_principal_root(root)
    elif kind == 'novelty' and root is None:
        state = support.load_candidate_state(final=True)
        duplicates = support.statement_duplicates(state.rows)
        if duplicates:
            raise support.G009Error('new statements duplicate a prior or current statement: '+repr(duplicates))
        report = expected_novelty(state)
    else:
        raise support.G009Error('unknown or incorrectly scoped final worker')
    gc.collect()
    if binding() != source_binding:
        raise support.G009Error('exact source/artifact bytes changed during verification')
    envelope = {'schema':SCHEMA,'kind':kind,'slug':checkpoints.SLUG,'root':root,'nonce':nonce,
        'binding_sha256':source_binding,'report':report,'limits':{'cpu':list(resource.getrlimit(resource.RLIMIT_CPU)),
        'wall_seconds':WALL_SECONDS,'max_rss_bytes':MAX_RSS_BYTES},'peak_rss_bytes':checkpoints.peak_rss_bytes()}
    payload = canonical_message(envelope)
    if len(payload) > MAX_STDOUT_BYTES:
        raise support.G009Error('worker report exceeds the original protocol byte bound')
    checkpoints.peak_rss_bytes()
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()
    checkpoints.peak_rss_bytes()
    return 0


def _collect_verified_syntax(collector, state, selected, report_bytes, source_binding):
    """One-way display transport, not a verifier or report-acceptance API.

    The controller calls this only after every actual worker succeeds. The
    callback receives immutable bytes and frozen syntax containers, never a
    mutable proof report or a certificate; its return value is ignored.
    """
    if not callable(collector) or type(report_bytes) is not bytes:
        raise support.G009Error('invalid one-way syntax callback transport')
    collector(state,selected,report_bytes)
    if binding() != source_binding:
        raise support.G009Error('sources changed during the display syntax callback')
    checkpoints.peak_rss_bytes()


def verify_in_fresh_windows(*, syntax_collector=None):
    if syntax_collector is not None and not callable(syntax_collector):
        raise support.G009Error('syntax_collector must be callable or None')
    source_binding = binding()
    pin = checkpoints.require_final_inventory()
    state = support.load_candidate_state(final=True)
    selected = support.select_support(state.rows,tuple(row.name for row in state.rows))
    novelty,peak = run_worker('novelty',None,source_binding,expected_novelty(state))
    family,used = run_worker('bundle',None,source_binding,checkpoints.expected_report(pin,state,selected))
    peak = max(peak,used)
    principals = []
    for name in checkpoints.PRINCIPAL_ROOTS:
        report,used = run_worker('root',name,source_binding,checkpoints.expected_root_report(pin,selected,name))
        principals.extend(report['principal_roots'])
        peak = max(peak,used)
    if binding() != source_binding:
        raise support.G009Error('sources changed across the complete fresh verification chain')
    if tuple(row['name'] for row in principals) != checkpoints.PRINCIPAL_ROOTS:
        raise support.G009Error('ordinary principal inventory is incomplete')
    result = {'schema':'peano-g009-local-research-checkpoint-v1','fresh_worker_count':8,
        'stored_receipt_is_proof_authority':False,'published':False,
        'alpha_admission_performed':False,'stable_admission_performed':False,
        'novelty':novelty,'checkpoint':family,'principal_roots':principals,
        'multiplicative_convolution_principals_checked':True,
        'peak_rss_bytes':max(peak,checkpoints.peak_rss_bytes())}
    if syntax_collector is not None:
        _collect_verified_syntax(syntax_collector,state,selected,
                                 canonical_message(result),source_binding)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',choices=('bundle','root','novelty'),help=argparse.SUPPRESS)
    for name in ('root','nonce','binding'):
        parser.add_argument('--'+name,help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        if not args.nonce or not args.binding or (args.worker == 'root') != (args.root is not None):
            parser.error('only a fully bound principal worker accepts an exact root')
        return worker(args.worker,args.root,args.nonce,args.binding)
    if args.root or args.nonce or args.binding:
        parser.error('private worker arguments need an explicit worker mode')
    resource.setrlimit(resource.RLIMIT_CPU,CPU_LIMITS)
    signal.alarm(CONTROLLER_WALL_SECONDS)
    print(support.canonical(verify_in_fresh_windows()).decode(),flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
