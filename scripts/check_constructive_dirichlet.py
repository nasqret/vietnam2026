#!/usr/bin/env python3
"""Fresh bounded HA, compiled-Lean and ordinary-root Dirichlet checks.

Twenty-one sequential jobs (whole-tranche novelty, five exact HA/Lean families
and fifteen ordinary principal certificates) each keep the original proof
window. The parent only authenticates bounded messages and formats a report.
No previous success receipt is a verification input.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
from hashlib import sha256
import os
from pathlib import Path
import re
import resource
import secrets
import signal
import sys

from check_constructive_bottom_layers import authoring_rss_bytes,canonical_report,check_receipt_bytes
import check_constructive_lower_continuation as transport
import constructive_dirichlet_checkpoints as checkpoints
import constructive_dirichlet_support as support
from peano_lab.engine.state import proof_metrics
from peano_lab.library.proof_bundle import decode_proof_bundle


ROOT=checkpoints.ROOT
SCRIPT=Path(__file__).resolve()
RECEIPT=ROOT/'research/arithmetic-library/artifacts/dirichlet-checkpoints-v1.json'
WORKER_SCHEMA='peano-lab-dirichlet-fresh-worker-v1'
CPU_LIMITS=(170,175)
WALL_SECONDS=180
PARENT_TIMEOUT_SECONDS=185
MAX_RSS_BYTES=1536*1024*1024
MAX_STDOUT_BYTES=128*1024
MAX_STDERR_BYTES=8*1024
EXPECTED_INVENTORY=(('finite-support',8),('dirichlet-convolution',40),('dirichlet-fubini',32),
                    ('dirichlet-units',25),('mobius-inversion',8))
ORDINARY_ROOTS_PER_FAMILY=3
CONTROLLER_WALL_SECONDS=(len(EXPECTED_INVENTORY)*(1+ORDINARY_ROOTS_PER_FAMILY)+1)*PARENT_TIMEOUT_SECONDS+WALL_SECONDS
CONTROL_SOURCES=(
    'scripts/check_constructive_dirichlet.py','scripts/constructive_dirichlet_checkpoints.py',
    'scripts/constructive_dirichlet_support.py','scripts/export_constructive_dirichlet.py',
    'scripts/check_constructive_lower_continuation.py','scripts/constructive_lower_continuation_checkpoints.py',
    'scripts/constructive_lower_continuation_support.py','scripts/check_constructive_bottom_layers.py',
    'scripts/constructive_bottom_layer_checkpoints.py','scripts/constructive_lower_tier_checkpoints.py',
    'scripts/constructive_lower_tier_support.py','peano-lab/py/peano_lab/library/campaign_bottom_layer_closure.py',
)

# These reviewed helpers depend only on the shared unchanged transport bounds,
# workspace and supplied arguments. No old module global is patched, and no
# historical registry, worker dispatcher or stored success report is reused.
if (transport.ROOT!=ROOT or transport.CPU_LIMITS!=CPU_LIMITS or transport.WALL_SECONDS!=WALL_SECONDS
        or transport.PARENT_TIMEOUT_SECONDS!=PARENT_TIMEOUT_SECONDS or transport.MAX_RSS_BYTES!=MAX_RSS_BYTES
        or transport.MAX_STDOUT_BYTES!=MAX_STDOUT_BYTES or transport.MAX_STDERR_BYTES!=MAX_STDERR_BYTES):
    raise RuntimeError('the inherited bounded transport contract changed')
AuditWorkerError=transport.AuditWorkerError
_canonical=transport._canonical
_decode_message=transport._decode_message
_capture_bounded=transport._capture_bounded
_validate_report=transport._validate_report


def _inventory():
    if (tuple((item.slug,item.frontier_count) for item in checkpoints.CHECKPOINTS)!=EXPECTED_INVENTORY
            or checkpoints.EXPECTED_FAMILIES!={name for name,_ in EXPECTED_INVENTORY}
            or any(len(item.principal_roots)!=ORDINARY_ROOTS_PER_FAMILY for item in checkpoints.CHECKPOINTS)):
        raise AuditWorkerError('the exact five-family Dirichlet inventory changed')
    rows=checkpoints.all_new_rows()
    if len(rows)!=113 or len({row.name for row in rows})!=113:
        raise AuditWorkerError('the exact 113 new statements changed')
    return rows


def _prior_checkpoints():
    return (*checkpoints.original.CHECKPOINTS,*support.previous.lower.CHECKPOINTS,*support.continuation.CHECKPOINTS)


def _binding():
    rows=_inventory();previous=support.previous_rows()
    if len(previous)!=421:
        raise AuditWorkerError('the three exact inherited research generations changed')
    controls=[]
    for relative in CONTROL_SOURCES:
        path=ROOT/relative;maximum=checkpoints.original.MAX_SOURCE_BYTES
        if not path.is_file() or path.is_symlink() or not 0<path.stat().st_size<=maximum:
            raise AuditWorkerError('an audit control source is not a bounded regular file')
        with path.open('rb') as stream:payload=stream.read(maximum+1)
        if not 0<len(payload)<=maximum:
            raise AuditWorkerError('an audit control source changed during its read')
        controls.append({'path':relative,'sha256':sha256(payload).hexdigest()})
    closure=checkpoints.closure
    closure._read_pinned(ROOT/closure.PARENT_CATALOG,closure.PARENT_CATALOG_BYTES,closure.PARENT_CATALOG_SHA256)
    for item in (*_prior_checkpoints(),*checkpoints.CHECKPOINTS):
        closure._read_pinned(ROOT/item.artifact,item.artifact_bytes,item.artifact_sha256)
    checkpoints.original._check_lean_binary()
    value={'controls':controls,'checkpoints':[asdict(item) for item in checkpoints.CHECKPOINTS],
           'prior_checkpoints':[asdict(item) for item in _prior_checkpoints()],
           'current_specs_sha256':closure._specs_digest(rows),'previous_specs_sha256':closure._specs_digest(previous),
           'parent':[closure.PARENT_CATALOG,closure.PARENT_CATALOG_BYTES,closure.PARENT_CATALOG_SHA256],
           'checker':[checkpoints.LEAN_BINARY_BYTES,checkpoints.LEAN_BINARY_SHA256]}
    return sha256(_canonical(value)).hexdigest()


def _expected_family_report(checkpoint, *, with_selection=False):
    """Derive exact message metadata independently, not a proof receipt."""
    if type(with_selection) is not bool:
        raise AuditWorkerError('with_selection must be an explicit Boolean')
    rows=_inventory();owned=checkpoints.load_rows(checkpoint)
    selected=support.select_support(rows,tuple(row.name for row in owned));closure=checkpoints.closure
    payload=closure._read_pinned(ROOT/checkpoint.artifact,checkpoint.artifact_bytes,checkpoint.artifact_sha256)
    bundle,_=decode_proof_bundle(payload.decode('utf-8'))
    positions={row.name:row.node_id for row in selected.plan.rows};by_name={row.name:row for row in owned}
    report={
        'slug':checkpoint.slug,'membership':'local_non_admitting_checkpoint',
        'admitted_to_alpha':False,'alpha_checked_use':False,'stable_member':False,
        'new_theorem_count':len(owned),'ordered_new_names_sha256':sha256('\n'.join(row.name for row in owned).encode()).hexdigest(),
        'new_specs_sha256':checkpoint.frontier_specs_sha256,'complete_non_alpha_specs_sha256':selected.plan.frontier_specs_sha256,
        'new_theorem_dependency_edges':sum(len(row.dependencies) for row in owned),
        'new_theorem_tactic_commands':sum(len(row.script) for row in owned),
        'sources':[{'path':pin.path,'sha256':pin.sha256,'factory':pin.factory} for pin in checkpoint.modules],
        'rfc':checkpoint.rfc,
        'support':{
            'prior_bottom_layer_theorems':list(selected.bottom_support),'prior_lower_tier_theorems':list(selected.lower_support),
            'prior_lower_continuation_theorems':list(selected.local_support),'current_cross_track_theorems':list(selected.current_support),
            'prior_bottom_layer_count':len(selected.bottom_support),'prior_lower_tier_count':len(selected.lower_support),
            'prior_lower_continuation_count':len(selected.local_support),'published_non_admitted_count':len(selected.published_support),
            'local_non_admitted_count':len(selected.local_support),'current_cross_track_count':len(selected.current_support),
            'alpha_v30_count':len(selected.plan.rows)-len(selected.frontier),'counted_as_new_owned_theorems':False,
        },
        'bundle':{
            'path':checkpoint.artifact,'bytes':checkpoint.artifact_bytes,'sha256':checkpoint.artifact_sha256,
            'nodes_including_packaging_root':len(bundle.nodes),
            'dependency_edges_including_packaging':sum(len(node.dependencies) for node in bundle.nodes),
            'body_proof_nodes':sum(proof_metrics(node.body)[0] for node in bundle.nodes),'packaging_root_id':bundle.root,
            'original_ha_checked':True,'independent_lean_checked':True,
        },
        'all_maximal_owned_roots':list(selected.plan.root_names),
        'principal_roots':[{'name':name,'node_id':positions[name],
            'statement_sha256':sha256(by_name[name].statement.encode()).hexdigest(),'complete_ordinary_ha_checked':False}
            for name in checkpoint.principal_roots],
    }
    result=(report,selected) if with_selection else report
    del bundle,payload,selected
    gc.collect()
    return result


def _expected_novelty_report():
    rows=_inventory()
    return {'new_theorems':113,'prior_theorems':3643,'ordered_specs_sha256':checkpoints.closure._specs_digest(rows),
            'duplicates':[],'exact_ast_novelty_checked':True}


def _expected_root_report(family_report,name):
    roots=[row for row in family_report['principal_roots'] if row['name']==name]
    if len(roots)!=1:raise AuditWorkerError('unknown exact ordinary principal')
    return {'slug':family_report['slug'],'bundle_sha256':family_report['bundle']['sha256'],
            'principal_roots':[{**roots[0],'complete_ordinary_ha_checked':True}]}


def _validate_message(payload,*,kind,slug,nonce,binding,expected):
    value=_decode_message(payload)
    if set(value)!={'schema','kind','slug','nonce','binding_sha256','limits','peak_rss_bytes','report'}:
        raise AuditWorkerError('worker envelope fields changed')
    wanted={'schema':WORKER_SCHEMA,'kind':kind,'slug':slug,'nonce':nonce,'binding_sha256':binding,
            'limits':{'cpu':list(CPU_LIMITS),'wall_seconds':WALL_SECONDS,'max_rss_bytes':MAX_RSS_BYTES}}
    if _canonical({key:value[key] for key in wanted})!=_canonical(wanted):
        raise AuditWorkerError('stale, foreign, or incorrectly limited worker response')
    peak=value['peak_rss_bytes']
    if type(peak) is not int or not 0<peak<=MAX_RSS_BYTES:
        raise AuditWorkerError('worker exceeded the original RSS ceiling')
    _validate_report(value['report'],expected,family=kind=='root')
    return value['report'],peak


def _run_worker(kind,slug,binding,expected,*,root=None):
    nonce=secrets.token_hex(32)
    command=[sys.executable,str(SCRIPT),'--worker',kind,'--slug',slug,'--nonce',nonce,'--binding',binding]
    if root is not None:command.extend(('--root',root))
    environment=os.environ.copy()
    environment.update(PYTHONPATH=os.pathsep.join((str(ROOT/'peano-lab/py'),str(ROOT/'scripts'))),
                       PYTHONMALLOC='malloc',PYTHONNOUSERSITE='1')
    label=f'{kind}: {slug}'+(f' / {root}' if root is not None else '')
    print(f'Checking {label}',file=sys.stderr,flush=True)
    payload=_capture_bounded(command,environment)
    report,peak=_validate_message(payload,kind=kind,slug=slug,nonce=nonce,binding=binding,expected=expected)
    print(f'Verified {label}; peak RSS {peak} bytes',file=sys.stderr,flush=True)
    return report,peak


def _worker(kind,slug,nonce,binding,root=None):
    resource.setrlimit(resource.RLIMIT_CPU,CPU_LIMITS);signal.alarm(WALL_SECONDS)
    if re.fullmatch(r'[0-9a-f]{64}',nonce or '') is None or re.fullmatch(r'[0-9a-f]{64}',binding or '') is None:
        raise AuditWorkerError('invalid private worker invocation')
    if _binding()!=binding:
        raise AuditWorkerError('worker source or inventory differs from its controller')
    if kind in ('family','root'):
        selected=[item for item in checkpoints.CHECKPOINTS if item.slug==slug]
        if len(selected)!=1:raise AuditWorkerError('unknown exact family worker')
        if kind=='family' and root is None:
            evidence=checkpoints.verify_checkpoint(selected[0],ordinary_roots=False);report=evidence.report
            del evidence
        elif kind=='root' and root in selected[0].principal_roots:
            report=checkpoints.verify_principal_root(selected[0],root)
        else:
            raise AuditWorkerError('unknown or incorrectly scoped ordinary principal')
        gc.collect()
    elif kind=='novelty' and slug=='all' and root is None:
        duplicates=support.statement_duplicates(_inventory())
        if duplicates:raise AuditWorkerError(f'the exact tranche contains duplicate statements: {duplicates!r}')
        report=_expected_novelty_report()
    else:
        raise AuditWorkerError('unknown exact audit job')
    if _binding()!=binding:
        raise AuditWorkerError('sources or inventory changed during actual verification')
    envelope={'schema':WORKER_SCHEMA,'kind':kind,'slug':slug,'nonce':nonce,'binding_sha256':binding,'report':report,
              'limits':{'cpu':list(resource.getrlimit(resource.RLIMIT_CPU)),'wall_seconds':WALL_SECONDS,'max_rss_bytes':MAX_RSS_BYTES},
              'peak_rss_bytes':authoring_rss_bytes()}
    if len(_canonical(envelope))>MAX_STDOUT_BYTES:raise AuditWorkerError('the actual worker report exceeded its protocol bound')
    envelope['peak_rss_bytes']=authoring_rss_bytes();payload=_canonical(envelope);authoring_rss_bytes()
    sys.stdout.buffer.write(payload);sys.stdout.buffer.flush();authoring_rss_bytes()
    return 0


def verify_in_fresh_windows(*, syntax_collector=None):
    """Check all actual proofs, optionally retaining their display syntax.

    The collector receives only source-selected plans and immutable expected
    metadata, never a kernel receipt or cached proof certificate. It is called
    only after every fresh job, the final source binding and aggregation pass.
    This avoids recomputing the same expensive support cones during rendering.
    """
    if syntax_collector is not None and not callable(syntax_collector):
        raise AuditWorkerError('syntax_collector must be callable or absent')
    binding=_binding()
    _,peak=_run_worker('novelty','all',binding,_expected_novelty_report());reports=[];retained=[]
    for item in checkpoints.CHECKPOINTS:
        if syntax_collector is None:
            expected=_expected_family_report(item)
        else:
            expected,selected=_expected_family_report(item,with_selection=True)
        report,worker_peak=_run_worker('family',item.slug,binding,expected)
        peak=max(peak,worker_peak);principals=[]
        for name in item.principal_roots:
            root_report,worker_peak=_run_worker('root',item.slug,binding,_expected_root_report(expected,name),root=name)
            principals.extend(root_report['principal_roots']);peak=max(peak,worker_peak)
        # Only authenticated fresh root messages fill these fields. The
        # original HA/Lean family report itself makes no ordinary-root claim.
        reports.append({**report,'principal_roots':principals})
        if syntax_collector is not None:
            retained.append((item,selected,_canonical(expected)))
            del selected
    if _binding()!=binding:raise AuditWorkerError('sources or inventory changed across fresh audit windows')
    aggregate=checkpoints._aggregate_reports(reports)
    peak=max(peak,authoring_rss_bytes())
    if syntax_collector is not None:
        for item,selected,expected_bytes in retained:
            syntax_collector(item,selected,expected_bytes)
    return aggregate,max(peak,authoring_rss_bytes())


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument('--check',action='store_true');group.add_argument('--write',action='store_true')
    parser.add_argument('--worker',choices=('family','root','novelty'),help=argparse.SUPPRESS)
    for name in ('slug','nonce','binding','root'):parser.add_argument('--'+name,help=argparse.SUPPRESS)
    args=parser.parse_args(argv)
    if args.worker:
        if args.check or args.write or not all((args.slug,args.nonce,args.binding)):
            parser.error('private workers cannot read or write audit receipts')
        if (args.worker=='root')!=(args.root is not None):parser.error('only root workers require an exact principal name')
        return _worker(args.worker,args.slug,args.nonce,args.binding,args.root)
    if any((args.slug,args.nonce,args.binding,args.root)):parser.error('private arguments require an exact worker mode')
    resource.setrlimit(resource.RLIMIT_CPU,CPU_LIMITS);signal.alarm(CONTROLLER_WALL_SECONDS)
    report,workers_peak=verify_in_fresh_windows();encoded=canonical_report(report)
    if args.check:check_receipt_bytes(RECEIPT,encoded)
    authoring_rss_bytes()
    if args.write:
        RECEIPT.parent.mkdir(parents=True,exist_ok=True)
        with RECEIPT.open('x',encoding='utf-8') as stream:stream.write(encoded)
    for item in report['checkpoints']:
        print(f"{item['slug']}: {item['new_theorem_count']} new theorems; complete HA, independent Lean, ordinary roots PASS")
    print(f"Exact AST novelty: {report['new_theorems']} new statements distinct from all 3643 prior rows and each other.")
    print(f'Peak RSS {max(workers_peak,authoring_rss_bytes())} bytes; Alpha 3222 / Stable 432 unchanged; no admission or publication.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
