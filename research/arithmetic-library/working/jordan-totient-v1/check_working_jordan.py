#!/usr/bin/env python3
"""Separate original-bounded complete Jordan authoring/HA+Lean/ordinary gates.

Each invocation has one original clock. Stages are independent complete proof
bundles, not continuations of a timed-out check. No observation is proof input.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict,dataclass
import gc
from hashlib import sha256
import os
from pathlib import Path
import resource
import signal
import stat
import time

STARTED=time.monotonic()
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)
import working_jordan_support as support


@dataclass(frozen=True,slots=True)
class ArtifactPin:
    path:str
    bytes:int
    sha256:str
    nodes:int
    edges:int
    body_nodes:int


# Actual final bytes only; no planned artifact or stored successful receipt.
FINAL_ARTIFACT: ArtifactPin | None = ArtifactPin(
    'research/arithmetic-library/working/jordan-totient-v1/artifacts/working-jordan-prefix-75-proof-bundle-v1.json',
    847318,'47754de334ada44e4eb9869358f4f3d0ec659083d529894d8cdc8e9fed30eca0',239,591,14462)


def resources():
    support.require(resource.getrlimit(resource.RLIMIT_CPU)==(170,175) and time.monotonic()-STARTED<=180,
                    'original CPU/wall bounds changed')
    from check_constructive_bottom_layers import authoring_rss_bytes
    return authoring_rss_bytes()


def directory_identity(path):
    info=path.lstat()
    support.require(stat.S_ISDIR(info.st_mode),'linked or non-directory output ancestor')
    return info.st_dev,info.st_ino,info.st_mode


def destination(through,path):
    path=Path(path).absolute()
    support.require('..' not in path.parts and path==support.stage_path(through),'not the exact new phase output')
    support.require(not path.exists() and not path.is_symlink(),'existing proof data is never overwritten')
    for parent in path.parent.parents:directory_identity(parent)
    if path.parent.exists() or path.parent.is_symlink():
        directory_identity(path.parent)
        support.require(path.parent.lstat().st_uid==os.getuid(),'foreign-owned output directory')
    return path


def write_exclusive(through,path,payload,binding):
    support.require(type(payload) is bytes and 0<len(payload)<=support.MAX_BYTES,'invalid bounded proof payload')
    path=destination(through,path);path.parent.mkdir(exist_ok=True)
    ancestors=tuple((p,directory_identity(p)) for p in (path.parent,*path.parent.parents))
    directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    created=None
    try:
        opened=os.fstat(directory)
        support.require((opened.st_dev,opened.st_ino,opened.st_mode)==ancestors[0][1] and opened.st_uid==os.getuid(),
                        'owned output directory changed')
        resources()
        descriptor=os.open(path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=directory)
        with os.fdopen(descriptor,'wb') as stream:
            info=os.fstat(stream.fileno());created=(info.st_dev,info.st_ino)
            support.require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1,'foreign output inode')
            support.require(stream.write(payload)==len(payload),'incomplete proof-data write');stream.flush()
        support.require(all(directory_identity(p)==identity for p,identity in ancestors),'output ancestor changed')
        support.require(support.raw(path)==payload and support.state_binding()==binding,'output/source changed during write')
        resources()
    except BaseException:
        if created is not None:
            info=os.stat(path.name,dir_fd=directory,follow_symlinks=False)
            support.require(stat.S_ISREG(info.st_mode) and (info.st_dev,info.st_ino)==created and
                            info.st_uid==os.getuid() and info.st_nlink==1,'refuse rollback of replaced output')
            os.unlink(path.name,dir_fd=directory)
        raise
    finally:os.close(directory)


def verify_registration(through,artifact_sha):
    path=support.stage_path(through)
    if through==75:
        pin=FINAL_ARTIFACT
        support.require(type(pin) is ArtifactPin,'no actual final artifact registered')
        support.require(pin.path==path.relative_to(support.ROOT).as_posix() and pin.nodes==239 and pin.edges==591 and
                        type(pin.body_nodes) is int and pin.body_nodes>0,'partial/malformed final registration')
        support.require(artifact_sha==pin.sha256,'CLI/final literal pin differs')
        payload=support.read_pin(support.FilePin(pin.path,pin.bytes,pin.sha256))
    else:
        support.require(type(artifact_sha) is str and len(artifact_sha)==64 and
                        all(c in '0123456789abcdef' for c in artifact_sha),'actual intermediate data SHA required')
        payload=support.raw(path)
        support.require(sha256(payload).hexdigest()==artifact_sha,'intermediate data SHA differs')
    return payload


def parent_pins(closure):
    """Authenticate the original catalog and its exact transitive providers.

    This is called only in the explicit original-parent window, never by the
    lightweight source inventory. These byte pins convey no proof acceptance.
    """
    pins=(support.FilePin(closure.PARENT_CATALOG,closure.PARENT_CATALOG_BYTES,closure.PARENT_CATALOG_SHA256),
          *(support.FilePin(p.path,p.bytes,p.sha256) for p in closure.parent_snapshot().documents))
    support.require(len({p.path for p in pins})==len(pins),'duplicate original parent document')
    for pin in pins:support.read_pin(pin)
    return pins


def run(task,through,output=None,artifact_sha=None,name=None):
    support.stage_path(through)
    support.require(task in ('source','inspect','author','bundle','root'),'unknown verification task')
    support.require((task=='author')==(output is not None),'only authoring accepts an explicit output')
    support.require((task in ('bundle','root'))==(artifact_sha is not None),'only verification consumes actual artifact SHA')
    support.require((task=='root')==(name is not None),'only ordinary replay accepts a theorem name')
    if task=='author':output=destination(through,output) # Before source/parent/proof work.
    if task=='root':support.require(through==75 and name in support.PRINCIPALS,'unknown final maximal root')
    if task in ('bundle','root'):verify_registration(through,artifact_sha) # Reject absent/unpinned data before parent work.
    before=support.state_binding()
    owned,source_rows,roots=support.source_selection(through)
    report=dict(schema='jordan-complete-checkpoint-observation-v1',task=task,through=through,proof_authority=False,
                source_binding=before,owned_count=len(owned),theorem_count=len(source_rows),maximal_roots=roots,
                original_ha_checked=False,independent_same_byte_lean_checked=False,ordinary_empty_context_checked=False,
                complete_checkpoint_acceptance=False,alpha_admitted=False,stable_changed=False)
    if task!='source':
        from peano_lab.library import campaign_bottom_layer_closure as closure
        from peano_lab.library.proof_bundle import decode_proof_bundle,encode_proof_bundle
        original_parent_pins=parent_pins(closure)
        owned,rows,frontier,plan=support.execution_selection(through)
        report.update(plan=asdict(plan),frontier_specs_sha256=closure._specs_digest(frontier),
                      original_parent_plan_checked=True,original_parent_documents=[asdict(p) for p in original_parent_pins])
        if task=='author':
            paths=support.required_seeds(through)
            seed_pins=[support.actual_pin(p) for p in paths]
            coverage=support.seed_coverage(through)
            support.require(tuple(closure._validate_seeds(paths))==paths,'original seed path policy changed')
            result=closure.assemble_bottom_layer_bundle(frontier,seed_bundles=paths,batch_size=1,
                report=lambda message:print(message,flush=True))
            nodes,edges,count=support.METRICS[through]
            support.require(result.plan==plan and result.receipt.node_count==result.receipt.kernel_calls==nodes+1 and
                            result.receipt.dependency_edges==edges+count,'authoring incomplete or wrong exact cone')
            payload=encode_proof_bundle(result.bundle,result.target).encode()
            support.require([support.actual_pin(p) for p in paths]==seed_pins,'actual seed bytes changed during authoring')
            support.require(parent_pins(closure)==original_parent_pins,'original parent changed during authoring')
            support.require(support.state_binding()==before,'source changed during authoring');resources()
            write_exclusive(through,output,payload,before)
            report.update(original_ha_checked=True,receipt=asdict(result.receipt),seed_coverage=coverage,
                          artifact=asdict(support.actual_pin(output)))
        elif task in ('bundle','root'):
            payload=verify_registration(through,artifact_sha)
            bundle,target=decode_proof_bundle(payload.decode())
            nodes,edges,count=support.METRICS[through]
            support.require(len(bundle.nodes)==nodes+1 and bundle.root==nodes,'partial stage artifact')
            if task=='bundle':
                receipt=closure.check_bottom_layer_bundle(frontier,bundle,target)
                support.require(receipt.node_count==receipt.kernel_calls==nodes+1 and receipt.dependency_edges==edges+count,
                                'whole native stage inventory differs')
                if through==75:support.require(receipt.total_body_nodes==FINAL_ARTIFACT.body_nodes,'final body inventory differs')
                import constructive_bottom_layer_checkpoints as independent
                checkpoint=independent.Checkpoint(f'working-jordan-{through}',(),support.stage_path(through).relative_to(support.ROOT).as_posix(),
                    len(payload),artifact_sha,len(frontier),tuple(plan.root_names),'',closure._specs_digest(frontier))
                independent._lean_check(checkpoint,receipt.node_count,bundle.root,payload)
                report.update(original_ha_checked=True,independent_same_byte_lean_checked=True,receipt=asdict(receipt))
            else:
                from peano_lab.kernel.checker import check
                from peano_lab.library.theorems import _closed_formula
                exact=next(r for r in owned if r.name==name)
                del payload;gc.collect()
                proof=closure.replay_bottom_layer_theorem(frontier,name,bundle,target)
                formula=_closed_formula(exact.statement)
                support.require(proof.spec==exact and proof.formula==formula and check((),proof.certificate,formula),
                                'original ordinary empty-context certificate rejected')
                report.update(ordinary_empty_context_checked=True,root=name,ordinary_nodes=proof.proof_nodes)
            verify_registration(through,artifact_sha)
            report['artifact']=asdict(support.actual_pin(support.stage_path(through)))
        support.require(parent_pins(closure)==original_parent_pins,'final original parent documents differ')
    support.require(support.state_binding()==before,'final before/after source binding differs')
    report.update(passed=True,seconds=time.monotonic()-STARTED,peak_rss_bytes=resources(),cpu_limits=[170,175],wall_alarm_seconds=180)
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task',choices=('source','inspect','author','bundle','root'),required=True)
    parser.add_argument('--through',type=int,choices=support.PHASES,required=True)
    parser.add_argument('--output',type=Path);parser.add_argument('--artifact-sha256');parser.add_argument('--name')
    args=parser.parse_args(argv)
    print(support.canonical(run(args.task,args.through,args.output,args.artifact_sha256,args.name)).decode(),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
