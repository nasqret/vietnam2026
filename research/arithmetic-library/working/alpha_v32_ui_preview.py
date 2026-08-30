"""Private UI diagnostics over non-authorizing actual metadata fixtures.

No public builder is called, no release object is minted and no generated file
is installed. The genuine fresh proof/publication pipeline remains mandatory.
"""

from __future__ import annotations

import argparse
import gc
import inspect
import os
from pathlib import Path
import resource
import signal
import sys
from tempfile import TemporaryDirectory
import time
import traceback
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "peano-lab/py")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("research", "completed", "historical"))
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(390)
    started = time.monotonic()
    import test_verify_peano_library_channels_v32 as metadata
    import constructive_research_publication_v32 as publication
    from tests import test_constructive_research_publication_v32 as ui
    runtime = metadata.current_runtime_metadata_only.__wrapped__()
    syntax_generator = metadata.syntax_metadata_only.__wrapped__()
    syntax = next(syntax_generator)
    projection_generator = metadata.metadata_projection_only.__wrapped__(runtime, syntax)
    observed = next(projection_generator)
    context = SimpleNamespace(catalog=observed.catalog, channels=observed.channels, families=observed.families,
        catalog_sha256=observed.manifest_hash, revision=observed.manifest_hash[:12],
        source_binding_sha256="0" * 64, render_source_binding_sha256="0" * 64,
        proofs_verified=False, scope="NON-AUTHORIZING PRIVATE UI DIAGNOSTIC")
    try:
        publication.require_live(context)
    except publication.PublicationError:
        pass
    else:
        raise AssertionError("non-authorizing diagnostic unexpectedly entered a public gate")
    gc.collect()
    print("PRIVATE UI DIAGNOSTIC metadata ready; no proof authority; seconds", time.monotonic()-started, flush=True)
    with TemporaryDirectory(prefix="non-authorizing-v32-ui-", dir="/private/tmp") as temporary:
        directory = Path(temporary)
        pid = os.fork()
        if pid == 0:
            result = 1
            try:
                resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
                signal.alarm(180)
                entries = publication._research_projection_entries(context) if args.phase == "research" else publication._older_projection_entries(context, args.phase)
                pins = {}
                for name, raw in entries:
                    assert publication.safe_relative(name) and name not in pins
                    assert type(raw) is bytes and 0 < len(raw) <= 64 * 1024 * 1024
                    destination = directory / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open("xb") as stream:
                        stream.write(raw)
                    pins[name] = {"bytes": len(raw), "sha256": publication.digest(raw)}
                print("PRIVATE UI rendered", args.phase, len(pins), "files; seconds", time.monotonic()-started, flush=True)
                actual = {"phase": args.phase, "context": context, "directory": directory,
                    "inventory": {"files": pins, "file_count": len(pins),
                        "html_count": sum(name.endswith(".html") for name in pins),
                        "total_bytes": sum(pin["bytes"] for pin in pins.values())}}
                drivers = ui.drivers()
                slugs = {"research": ui.RESEARCH, "completed": ui.COMPLETED, "historical": ui.HISTORICAL}[args.phase]
                count = 0
                for name, function in vars(ui).items():
                    if not name.startswith("test_"+args.phase+"_phase_"):
                        continue
                    arguments = inspect.signature(function).parameters
                    for slug in slugs if "slug" in arguments else (None,):
                        values = {args.phase: actual, "runtime": drivers, "slug": slug}
                        function(**{key: values[key] for key in arguments})
                        count += 1
                peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                assert 0 < peak <= 1536 * 1024 * 1024
                print("PRIVATE UI ONLY PASS", args.phase, count, "cases; RSS", peak,
                      "seconds", time.monotonic()-started, "NO PUBLICATION OR PROOF ADMISSION", flush=True)
                result = 0
            except BaseException:
                traceback.print_exc()
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(result)
        _, status = os.waitpid(pid, 0)
        for generator in (projection_generator, syntax_generator):
            try:
                next(generator)
            except StopIteration:
                pass
            else:
                raise AssertionError("metadata fixture did not finalize")
        return os.waitstatus_to_exitcode(status)


if __name__ == "__main__":
    raise SystemExit(main())
