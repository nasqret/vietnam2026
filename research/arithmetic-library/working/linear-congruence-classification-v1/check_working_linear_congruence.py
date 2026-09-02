#!/usr/bin/env python3
"""Fresh whole HA/same-byte Lean and separate ordinary maximal-root gates."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import gc
from hashlib import sha256
import resource
import signal
import time

_STARTED=time.monotonic()
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
import working_linear_congruence_support as support
from peano_lab.kernel.checker import check
from peano_lab.library.proof_bundle import decode_proof_bundle
from peano_lab.library.theorems import _closed_formula

@dataclass(frozen=True,slots=True)
class ArtifactPin:
    path: str
    bytes: int
    sha256: str
    nodes: int
    edges: int
    body_nodes: int

# Only an actually authored original-HA payload may replace this unset marker.
FINAL_ARTIFACT: ArtifactPin | None = ArtifactPin(
    'research/arithmetic-library/working/linear-congruence-classification-v1/artifacts/working-linear-congruence-prefix-12-proof-bundle-v1.json',
    542092,'983051afddc637a4e033546b8f3ddb8dc0ac22aa996b4e28b3822be8895576ad',215,647,13079)

def _resources():
    support._require(resource.getrlimit(resource.RLIMIT_CPU)==(170,175)
                     and time.monotonic()-_STARTED<=180,'original CPU/wall limits differ')
    return support.authoring_rss_bytes()

def require_final_inventory():
    pin=FINAL_ARTIFACT
    support._require(type(pin) is ArtifactPin,'no actual final artifact is registered')
    support._require(all(type(v) is int and v>0 for v in (pin.bytes,pin.nodes,pin.edges,pin.body_nodes))
                     and pin.nodes==215 and pin.edges==647 and pin.bytes<=support.MAX_BYTES
                     and support._safe_relative(pin.path) and support.ROOT/pin.path==support.stage_path()
                     and support._digest(pin.sha256),'malformed/partial final artifact registration')
    support.read_pin(support.FilePin(pin.path,pin.bytes,pin.sha256))
    return pin

def _load_final():
    pin=require_final_inventory()
    before=support.state_binding()
    selected,frontier,plan=support.execution_selection()
    payload=support.read_pin(support.FilePin(pin.path,pin.bytes,pin.sha256))
    bundle,target=decode_proof_bundle(payload.decode())
    support._require(len(bundle.nodes)==pin.nodes==len(plan.rows)+1 and bundle.root==214
                     and plan.root_names==support.PRINCIPAL_ROOTS,'incomplete actual artifact inventory')
    return pin,before,selected,frontier,plan,payload,bundle,target

def _finish(before):
    require_final_inventory()
    support._require(support.state_binding()==before,'actual proof inputs changed during verification')
    return _resources()

def verify_complete_bundle():
    pin,before,selected,frontier,plan,payload,bundle,target=_load_final()
    receipt=support.closure.check_bottom_layer_bundle(frontier,bundle,target)
    support._require((receipt.node_count,receipt.kernel_calls,receipt.dependency_edges,receipt.total_body_nodes)
                     ==(pin.nodes,pin.nodes,pin.edges,pin.body_nodes),'exact whole original-HA accounting differs')
    checkpoint=support.independent.Checkpoint('working-linear-congruence-classification',(),pin.path,
        pin.bytes,pin.sha256,12,support.PRINCIPAL_ROOTS,support.WORKING_RELATIVE+'/README.md',support.SPECS_SHA256)
    support.independent._lean_check(checkpoint,receipt.node_count,bundle.root,payload)
    return dict(schema='working-linear-congruence-bundle-check-v1',artifact_sha256=pin.sha256,
        nodes=receipt.node_count,edges=receipt.dependency_edges,body_nodes=receipt.total_body_nodes,
        kernel_calls=receipt.kernel_calls,source_binding=before,original_ha_checked=True,
        independent_same_byte_lean_checked=True,ordinary_principals_checked=False,
        global_current4092_novelty_checked=False,complete_checkpoint_acceptance=False,
        alpha_admission_performed=False,stable_admission_performed=False,peak_rss_bytes=_finish(before))

def verify_principal(name):
    support._require(type(name) is str and name in support.PRINCIPAL_ROOTS,'unknown ordinary principal')
    pin,before,selected,frontier,plan,payload,bundle,target=_load_final()
    exact=next(r for r in selected.owned if r.name==name)
    position=next(r.node_id for r in plan.rows if r.name==name)
    del selected,payload
    gc.collect()
    proof=support.closure.replay_bottom_layer_theorem(frontier,name,bundle,target)
    del bundle,target
    gc.collect()
    formula=_closed_formula(exact.statement)
    support._require(proof.spec==exact and proof.formula==formula and check((),proof.certificate,formula),
                     'exact ordinary empty-context original-HA check failed')
    return dict(schema='working-linear-congruence-principal-check-v1',name=name,node_id=position,
        statement_sha256=sha256(exact.statement.encode()).hexdigest(),artifact_sha256=pin.sha256,
        ordinary_certificate_nodes=proof.proof_nodes,complete_ordinary_ha_checked=True,
        independent_lean_checked=False,source_binding=before,complete_checkpoint_acceptance=False,
        alpha_admission_performed=False,stable_admission_performed=False,peak_rss_bytes=_finish(before))

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task',choices=('local','bundle','root'),required=True)
    parser.add_argument('--name',choices=support.PRINCIPAL_ROOTS)
    args=parser.parse_args(argv)
    if (args.task=='root') != (args.name is not None):parser.error('--name required only for root')
    if args.task=='local':report=support.local_manifest()
    elif args.task=='bundle':report=verify_complete_bundle()
    else:report=verify_principal(args.name)
    report.update(seconds=time.monotonic()-_STARTED,cpu_limits=[170,175],wall_alarm_seconds=180,
                  peak_rss_bytes=_resources())
    print(support.canonical(report).decode(),flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
