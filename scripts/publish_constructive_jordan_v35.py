#!/usr/bin/env python3
"""Publish v35 readers only from this invocation's complete fresh proof audit."""
from __future__ import annotations
import argparse
import resource
import signal
from constructive_alpha_v35_publication_process import publish_from_live_context


def stage_from_live_context(context, base, output, *, check):
    """Fork the original capability; saved JSON cannot start a delivery job."""
    import json
    import os
    from pathlib import Path
    import select
    from tempfile import TemporaryDirectory
    import time
    import constructive_jordan_publication_v35 as publication
    import constructive_alpha_v35_publication_process as process
    from stage_constructive_jordan_publication_v35 import stage, inventory, pin, read, MANIFEST
    context = publication.bind_live_context(context)
    publication.require_live(context)
    output = Path(output).absolute()
    process._regular_directory(output.parent)
    if not check and (output.exists() or output.is_symlink()):
        raise ValueError("refusing to replace an existing public delivery stage")
    with TemporaryDirectory(prefix=".jordan-delivery-", dir=output.parent) as temporary:
        candidate = output if check else Path(temporary) / "files"
        read_fd, write_fd = os.pipe()
        try:
            pid = os.fork()
        except BaseException:
            os.close(read_fd)
            os.close(write_fd)
            raise
        if pid == 0:
            os.close(read_fd)
            status = 1
            try:
                if process.ISOLATE_PHASE_GROUP:
                    os.setsid()
                resource.setrlimit(resource.RLIMIT_CPU, process.CPU_LIMITS)
                signal.signal(signal.SIGALRM, signal.SIG_DFL)
                signal.alarm(process.WALL_SECONDS)
                from threading import Thread
                def watch_rss():
                    while True:
                        try: process._rss_bytes()
                        except BaseException: os._exit(137)
                        time.sleep(0.05)
                Thread(target=watch_rss, daemon=True).start()
                result = stage(context, base, candidate, check=check)
                process._rss_bytes()
                raw = json.dumps(result, sort_keys=True).encode()
                if len(raw) > 4096: raise ValueError("oversized delivery result")
                os.write(write_fd, raw)
                status = 0
            except BaseException as error:
                import sys
                print("Jordan delivery failed: " + repr(error), file=sys.stderr, flush=True)
            finally:
                os.close(write_fd)
                os._exit(status)
        os.close(write_fd)
        reaped = False
        group_cleaned = False
        try:
            deadline = time.monotonic() + process.WALL_SECONDS
            result = bytearray()
            while True:
                if not select.select([read_fd], [], [], max(0, deadline-time.monotonic()))[0]:
                    raise TimeoutError("delivery exceeded its180-second window")
                block = os.read(read_fd, 4097-len(result))
                if not block: break
                result.extend(block)
                if len(result) > 4096: raise ValueError("oversized delivery pipe")
            while True:
                waited, status = os.waitpid(pid, os.WNOHANG)
                if waited: break
                if time.monotonic() >= deadline: raise TimeoutError("delivery child did not exit")
                time.sleep(0.01)
            reaped = True
            if process.ISOLATE_PHASE_GROUP:
                try: os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError: pass
            group_cleaned = True
            if status != 0: raise ValueError("bounded delivery child failed")
            observed = publication.strict_json(bytes(result))
            manifest_raw = read(candidate / MANIFEST)
            manifest = publication.strict_json(manifest_raw)
            expected = dict(manifest["current_files"], **{MANIFEST: pin(manifest_raw)})
            if (observed["manifest_sha256"] != pin(manifest_raw)["sha256"]
                    or inventory(candidate) != expected
                    or manifest["catalog_sha256"] != context.catalog_sha256
                    or manifest["source_binding_sha256"] != context.source_binding_sha256):
                raise ValueError("actual staged output differs from same-live release")
            publication.require_live(context)
            if time.monotonic() >= deadline:
                raise TimeoutError("delivery validation exceeded its180-second window")
            if not check: process._rename_new(candidate, output)
            return observed
        finally:
            os.close(read_fd)
            if not group_cleaned and process.ISOLATE_PHASE_GROUP:
                try: os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError: pass
            if not reaped:
                try: os.kill(pid, signal.SIGKILL)
                except ProcessLookupError: pass
                cleanup_deadline = time.monotonic() + process.CLEANUP_SECONDS
                while not os.waitpid(pid, os.WNOHANG)[0]:
                    if time.monotonic() >= cleanup_deadline:
                        raise TimeoutError("delivery cleanup exceeded five seconds")
                    time.sleep(0.01)

def _complete_from_live_audit(audit, args):
    """Post-audit controller; the original capability stays in this process."""
    import build_peano_library_channels_v35 as builder
    from verify_peano_library_channels_v35 import context_from_live_audit, verify_candidate_payloads
    print("Post-audit: construct exact candidate", flush=True)
    payloads, same = builder.build_payloads(audit)
    if same is not audit: raise ValueError("foreign audit returned during construction")
    print("Post-audit: independently verify candidate", flush=True)
    verify_candidate_payloads(payloads, audit)
    builder.check_or_write(payloads, check=not args.create_release or args.check)
    return {builder.relative(path): builder.digest(raw) for path, raw in payloads.items()}


def _publish_installed_from_live_audit(audit, args):
    import build_peano_library_channels_v35 as builder
    from verify_peano_library_channels_v35 import context_from_live_audit
    print("Post-audit: authenticate installed release", flush=True)
    context = context_from_live_audit(audit)
    print("Post-audit: generate and test canonical readers", flush=True)
    publish_from_live_context(context, check=args.check)
    context.require_unchanged()
    if args.stage_base:
        result = stage_from_live_context(context, args.stage_base, args.stage_output, check=args.check)
        print("Same-live Jordan delivery stage: " + str(result), flush=True)
        context.require_unchanged()
    paths = (builder.DEFAULT_ALPHA, builder.DEFAULT_DELTA, builder.DEFAULT_METRICS,
             builder.DEFAULT_GRAPH, builder.DEFAULT_CHANNELS, builder.DEFAULT_RECEIPT)
    return {builder.relative(path): builder.digest(builder.read_bytes(path)) for path in paths}


def _bounded_post_audit(audit, args, phase="admission"):
    """Inherit genuine proof authority, never deserialize it from an old run.

    Proof workers retain170/175 CPU and180 wall seconds. This separate
    controller receives the same CPU ceiling; its aggregate wall budget covers
    metadata work and waiting for the separately bounded reader/stage children.
    """
    import json
    import os
    import select
    import secrets
    import sys
    import time
    import traceback
    import check_alpha_v35_jordan as checking
    import build_peano_library_channels_v35 as builder
    if type(audit) is not checking.FreshProofAudit:
        raise ValueError("only this invocation's actual proof audit can continue")
    if phase not in ("admission", "publication"):
        raise ValueError("unknown post-audit phase")
    audit.require_unchanged()
    nonce = secrets.token_hex(32)
    timeout = 4 * checking.PARENT_TIMEOUT_SECONDS
    reader, writer = os.pipe()
    sys.stdout.flush(); sys.stderr.flush()
    try:
        pid = os.fork()
    except BaseException:
        os.close(reader); os.close(writer)
        raise
    if pid == 0:
        os.close(reader)
        status = 1
        try:
            os.setsid()
            resource.setrlimit(resource.RLIMIT_CPU, checking.CPU_LIMITS)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            signal.alarm(timeout)
            import constructive_alpha_v35_publication_process as process
            process.ISOLATE_PHASE_GROUP = False
            # CPU-time RSS checks keep this forking coordinator single-threaded.
            def rss_tick(*unused):
                checking.authoring_rss_bytes()
            signal.signal(signal.SIGVTALRM, rss_tick)
            signal.setitimer(signal.ITIMER_VIRTUAL, 0.25, 0.25)
            files = (_complete_from_live_audit(audit, args) if phase == "admission"
                     else _publish_installed_from_live_audit(audit, args))
            checking.authoring_rss_bytes()
            result = json.dumps(dict(nonce=nonce, phase=phase, binding=audit.binding, files=files), sort_keys=True).encode()
            if len(result) > 4096: raise ValueError("oversized controller result")
            os.write(writer, result)
            status = 0
        except BaseException:
            traceback.print_exc()
        finally:
            os.close(writer)
            sys.stdout.flush(); sys.stderr.flush()
            os._exit(status)
    os.close(writer)
    reaped, grouped = False, False
    deadline = time.monotonic() + timeout
    try:
        result = bytearray()
        while True:
            if not select.select([reader], [], [], max(0, deadline-time.monotonic()))[0]:
                raise TimeoutError("post-audit controller deadline exceeded")
            block = os.read(reader, 4097-len(result))
            if not block: break
            result.extend(block)
            if len(result) > 4096: raise ValueError("oversized controller pipe")
        while True:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited: break
            if time.monotonic() >= deadline: raise TimeoutError("controller did not exit")
            time.sleep(0.01)
        reaped = True
        try: os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError: pass
        grouped = True
        if status != 0: raise ValueError("bounded post-audit controller failed: " + str(status))
        value = json.loads(result)
        paths = (builder.DEFAULT_ALPHA, builder.DEFAULT_DELTA, builder.DEFAULT_METRICS,
                 builder.DEFAULT_GRAPH, builder.DEFAULT_CHANNELS, builder.DEFAULT_RECEIPT)
        actual = {builder.relative(path): builder.digest(builder.read_bytes(path)) for path in paths}
        if value != dict(nonce=nonce, phase=phase, binding=audit.binding, files=actual):
            raise ValueError("controller output differs from this live invocation")
        audit.require_unchanged()
        if time.monotonic() >= deadline: raise TimeoutError("controller validation exceeded deadline")
        checking.authoring_rss_bytes()
    finally:
        os.close(reader)
        if not grouped:
            try: os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError: pass
        if not reaped:
            try: os.kill(pid, signal.SIGKILL)
            except ProcessLookupError: pass
            end = time.monotonic() + 5
            while not os.waitpid(pid, os.WNOHANG)[0]:
                if time.monotonic() >= end: raise TimeoutError("controller cleanup exceeded five seconds")
                time.sleep(0.01)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--create-release",action="store_true")
    parser.add_argument("--stage-base",type=str)
    parser.add_argument("--stage-output",type=str)
    args=parser.parse_args(argv)
    if bool(args.stage_base) != bool(args.stage_output):
        parser.error("--stage-base and --stage-output are required together")
    import build_peano_library_channels_v35 as builder
    import check_alpha_v35_jordan as audit_module
    resource.setrlimit(resource.RLIMIT_CPU,audit_module.CPU_LIMITS)
    signal.alarm(audit_module.EXPECTED_JOB_COUNT*audit_module.PARENT_TIMEOUT_SECONDS+7*audit_module.WALL_SECONDS)
    builder.preflight_inputs()
    audit = audit_module.verify_in_fresh_windows()
    _bounded_post_audit(audit, args)
    _bounded_post_audit(audit, args, phase="publication")
    print("Verified Alpha v35 publication:4318 admissions, Stable432,95 new Jordan theorems; prime-power counting/product and G091 remain open.")
    return 0
if __name__=="__main__":raise SystemExit(main())
