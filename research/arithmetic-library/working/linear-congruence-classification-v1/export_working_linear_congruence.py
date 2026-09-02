#!/usr/bin/env python3
"""One original-bounded, exclusive, dependency-complete authoring stage."""
from __future__ import annotations
import argparse
from hashlib import sha256
import os
from pathlib import Path
import resource
import signal
import stat
import time
_STARTED=time.monotonic()
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
import working_linear_congruence_support as support
from check_constructive_bottom_layers import authoring_rss_bytes
CPU_LIMITS,WALL_SECONDS=(170,175),180
ARTIFACT_DIRECTORY=support.ARTIFACT_DIRECTORY
OUTPUT_PREFIX=support.OUTPUT_PREFIX

def _directory_identity(path):
    value = path.lstat()
    support._require(stat.S_ISDIR(value.st_mode), "proof output has a linked or non-directory ancestor")
    return value.st_dev, value.st_ino, value.st_mode


def destination(value):
    support._require(isinstance(value, (str, Path)), "one exact new proof-data path is required")
    path = Path(value).absolute()
    support._require(".." not in path.parts and path.parent == ARTIFACT_DIRECTORY
                     and path in tuple(support.stage_path(through) for through in support.PHASES)
                     and support._safe_relative(path.name),
                     "proof data must use the one exact new stage basename")
    support._require(not path.exists() and not path.is_symlink(),
                     "existing mathematical proof data is never overwritten")
    for parent in ARTIFACT_DIRECTORY.parents:
        _directory_identity(parent)
    if ARTIFACT_DIRECTORY.exists() or ARTIFACT_DIRECTORY.is_symlink():
        _directory_identity(ARTIFACT_DIRECTORY)
        support._require(ARTIFACT_DIRECTORY.lstat().st_uid == os.getuid(),
                         "the new proof-data directory has a foreign owner")
    return path


def _resources():
    support._require(resource.getrlimit(resource.RLIMIT_CPU) == CPU_LIMITS
                     and time.monotonic() - _STARTED <= WALL_SECONDS,
                     "the original authoring CPU/wall limits changed")
    return authoring_rss_bytes()


def write_exclusive(path, payload, binding):
    """Owned no-follow output; failed writes remove only the newly owned inode."""
    support._require(type(payload) is bytes and 0 < len(payload) <= support.MAX_BYTES,
                     "proof-data bytes exceed the unchanged payload ceiling")
    path = destination(path)
    ARTIFACT_DIRECTORY.mkdir(exist_ok=True)
    ancestors = tuple((parent, _directory_identity(parent))
                      for parent in (ARTIFACT_DIRECTORY, *ARTIFACT_DIRECTORY.parents))
    support._require(all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")),
                     "the original safe exclusive output flags are unavailable")
    descriptor = os.open(ARTIFACT_DIRECTORY, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    created = None
    try:
        opened = os.fstat(descriptor)
        support._require((opened.st_dev, opened.st_ino, opened.st_mode) == ancestors[0][1]
                         and opened.st_uid == os.getuid(), "the exact owned output directory changed")
        _resources()
        target = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=descriptor)
        with os.fdopen(target, "wb") as stream:
            info = os.fstat(stream.fileno())
            created = (info.st_dev, info.st_ino)
            support._require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
                             "the exclusive proof output is not an owned regular inode")
            support._require(stream.write(payload) == len(payload), "the exclusive proof-data write was incomplete")
            stream.flush()
        for parent, identity in ancestors:
            support._require(_directory_identity(parent) == identity,
                             "an output ancestor changed during the exclusive write")
        support.check_pin(support.FilePin(path.relative_to(support.ROOT).as_posix(), len(payload),
                                         sha256(payload).hexdigest()), support.ROOT, support.MAX_BYTES)
        support._require(support.state_binding() == binding, 'source binding changed during exclusive output')
        _resources()
    except BaseException:
        if created is not None:
            info = os.stat(path.name, dir_fd=descriptor, follow_symlinks=False)
            support._require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                             and info.st_nlink == 1 and (info.st_dev, info.st_ino) == created,
                             "rollback refuses to remove a changed or foreign output inode")
            os.unlink(path.name, dir_fd=descriptor)
        raise
    finally:
        os.close(descriptor)



def export_authoring_bundle(output):
    output=destination(output)
    before=support.state_binding()
    selected,frontier,plan=support.execution_selection()
    coverage=support.seed_coverage(selected)
    support._require(not coverage['missing_names'],'literal actual seed does not cover every inherited target')
    paths=tuple(support.ROOT/p.path for p in support.SEED_PINS)
    support._require(tuple(support.closure._validate_seeds(paths))==paths,'original seed path validation differs')
    result=support.closure.assemble_bottom_layer_bundle(frontier,seed_bundles=paths,batch_size=1,
        report=lambda message:print(message,flush=True))
    _resources()
    receipt=result.receipt
    support._require(result.plan==plan and receipt.node_count==receipt.kernel_calls==215
                     and receipt.dependency_edges==647 and receipt.total_body_nodes>0,
                     'original whole-HA receipt differs from exact inventory')
    payload=support.closure.encode_proof_bundle(result.bundle,result.target).encode()
    support._require(support.state_binding()==before,'sources changed during original HA authoring')
    write_exclusive(output,payload,before)
    return dict(schema='working-linear-congruence-authoring-v1',
        artifact=output.relative_to(support.ROOT).as_posix(),bytes=len(payload),sha256=sha256(payload).hexdigest(),
        nodes=receipt.node_count,edges=receipt.dependency_edges,body_nodes=receipt.total_body_nodes,
        original_kernel_calls=receipt.kernel_calls,new_rows=12,inherited_rows=202,
        owned_specs_sha256=support.SPECS_SHA256,
        owned_original_stream_specs_sha256=support.closure._specs_digest(selected.owned),
        complete_source_dfs_specs_sha256=support.spec_digest(selected.complete_specs),
        frontier_original_stream_specs_sha256=support.closure._specs_digest(frontier),
        frontier_names=[r.name for r in frontier],maximal_roots=plan.root_names,
        artifact_positions=[dict(name=r.name,node_id=r.node_id,statement_sha256=r.statement_sha256,
                                dependencies=list(r.dependencies)) for r in plan.rows],
        source_binding=before,seed_coverage=coverage,
        draft_proof_data_only=True,original_ha_checked=True,independent_lean_checked=False,
        ordinary_principals_checked=False,global_current4092_novelty_checked=False,
        complete_checkpoint_acceptance=False,alpha_admission_performed=False,stable_admission_performed=False,
        seconds=time.monotonic()-_STARTED,peak_rss_bytes=_resources(),cpu_limits=list(CPU_LIMITS),wall_alarm_seconds=180)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    print(support.canonical(export_authoring_bundle(args.output)).decode(),flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())

