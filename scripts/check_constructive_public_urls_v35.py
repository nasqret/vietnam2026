#!/usr/bin/env python3
"""Observe real public URLs, without cachebusting or any proof authority.

Each batch is at most four sequential20s requests. Only an explicitly accepted
local delivery manifest authorizes comparisons; no network occurs on import.
"""
from hashlib import sha256
from html.parser import HTMLParser
import argparse
import json
from pathlib import Path
import resource
import signal
import subprocess
from tempfile import TemporaryDirectory
from time import monotonic
from urllib.parse import urljoin, urlsplit, urlunsplit

import check_constructive_delivery_v35 as stage

transport = stage.transport
ORIGIN = transport.ORIGIN
PAGES = (
    "jordan-totient/index.html",
    "jordan-totient/explorer/defined/tag/JT004B.html",
    "jordan-totient/explorer/tag/JT004B.html",
    "jordan-totient/explorer/defined/graph.html",
    "integer-linear-algebra/explorer/defined/tag/DL0071.html",
    "quadratic-reciprocity/explorer/defined/tag/PA00A7.html",
)
ENTRANCES = ("/proofs/", "/proofs/grand-campaign/", "/proofs/jordan-totient/")
BATCH_SIZE, BATCH_SECONDS, REQUEST_SECONDS, CLEANUP_SECONDS = 4, 90, 20, 5


def resolve_url(reference, base_url):
    """Keep the actual query; drop only fragments, which HTTP never sends."""
    if (type(reference) is not str or not reference or len(reference) > 4096
            or "\\" in reference or any(ord(c) <= 32 or ord(c) == 127 for c in reference)):
        raise ValueError("unsafe public URL reference")
    parts = urlsplit(urljoin(base_url, reference))
    if parts.scheme != "https" or parts.netloc != urlsplit(ORIGIN).netloc or not parts.path.startswith("/proofs/"):
        raise ValueError("public URL is outside the exact same-origin proofs tree")
    name = parts.path[len("/proofs/"):]
    if not name or name.endswith("/"): name += "index.html"
    transport.relative_path(name)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, "")), name


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if tag == "base": raise ValueError("unexpected HTML base changes public URL resolution")
        if tag == "link" and "stylesheet" in (values.get("rel") or "").split():
            self.rows.append(("stylesheet", values.get("href")))
        if tag == "script" and values.get("src"):
            self.rows.append(("script", values["src"]))
        if tag == "a" and values.get("href"):
            reference = values["href"]
            path = urlsplit(reference).path
            if path.endswith(("graph.html", "graph.json")):
                self.rows.append(("graph", reference))
            elif urlsplit(reference).query and (path.endswith("/") or path in (".", "..")):
                self.rows.append(("navigation", reference))
        for key in ("data-graph-json", "data-graph-url", "data-corpus-url"):
            if values.get(key): self.rows.append(("graph-payload", values[key]))


def source_binding():
    binding = stage.source_binding()
    files = dict(binding["files"])
    for name in ("check_constructive_public_urls_v35.py", "test_check_constructive_public_urls_v35.py"):
        path = stage.ROOT / "scripts" / name
        raw = stage.read_file(path, 1024*1024)
        files[path.relative_to(stage.ROOT).as_posix()] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    return dict(sha256=transport.digest_value(files), files=files)


def inventory(accepted):
    files, _ = stage.snapshot(accepted)
    observations = {}

    def add(reference, base_url, purpose, source):
        url, name = resolve_url(reference, base_url)
        if name not in files: raise ValueError("actual generated URL has no staged file: " + url)
        row = observations.setdefault(url, dict(url=url, stage_relative_path=name, expected=files[name], sources=[]))
        provenance = dict(page=source, purpose=purpose, reference=reference)
        if provenance not in row["sources"]: row["sources"].append(provenance)

    for path in ENTRANCES:
        add(path, ORIGIN + "/proofs/", "unversioned-entrance", None)
    for name in PAGES:
        url = ORIGIN + "/proofs/" + name
        add(url, url, "unversioned-sample", None)
        raw = stage.read_file(stage.STAGE / name, transport.MAX_FILE)
        if dict(bytes=len(raw), sha256=sha256(raw).hexdigest()) != files.get(name):
            raise ValueError("HTML extraction source differs from accepted staging")
        parser = Links()
        parser.feed(raw.decode("utf-8"))
        for purpose, reference in parser.rows:
            # Selected assets and graph links must remain inside the site. We
            # fail rather than silently follow an unexpected offsite resource.
            add(reference, url, purpose, name)
    rows = [observations[url] for url in sorted(observations)]
    if not rows or len(rows) > 128: raise ValueError("unexpected public URL inventory size")
    stage.selected_snapshot(files, sorted({row["stage_relative_path"] for row in rows}))
    return rows


def fetch_exact(row, batch_deadline):
    """Use strict curl with bounded disk outputs; never append a new query."""
    url, expected = row["url"], row["expected"]
    if resolve_url(url, url) != (url, row["stage_relative_path"]):
        raise ValueError("noncanonical public request row")
    start = monotonic()
    result = dict(url=url, stage_relative_path=row["stage_relative_path"], expected=expected,
                  sources=row["sources"], passed=False, status=None, effective_url=None,
                  curl_exit=None, body_bytes=0, body_sha256=None, headers="", stderr="", failure=None,
                  cleanup_failed=False)
    process = None
    try:
        deadline = min(start+REQUEST_SECONDS, batch_deadline)
        if deadline <= start: raise TimeoutError("public request deadline reached before launch")
        # Sequential child launch only: this pre-exec resource limiter never
        # forks from a thread pool. Each of the three temporary files is bounded
        # by the kernel even if a server omits Content-Length or sends junk.
        file_cap = max(expected["bytes"]+1, transport.MAX_HEADERS+1, transport.MAX_STDERR+1)
        def limit_files():
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_cap, file_cap))
        with TemporaryDirectory(prefix="peano-public-url-") as temporary:
            directory = Path(temporary)
            body_path, error_path, headers_path = (directory/name for name in ("body", "stderr", "headers"))
            command = transport.curl_command(url, headers_path, deadline-start)
            result["command"] = command
            try:
                with body_path.open("xb") as body, error_path.open("xb") as errors:
                    process = subprocess.Popen(command, stdout=body, stderr=errors, preexec_fn=limit_files)
                    process.wait(timeout=max(0.001, deadline-monotonic()))
            finally:
                if process is not None:
                    try:
                        if process.poll() is None: process.kill()
                        process.wait(timeout=min(CLEANUP_SECONDS, max(0.001, batch_deadline+CLEANUP_SECONDS-monotonic())))
                    except (OSError, subprocess.SubprocessError):
                        result["cleanup_failed"] = True
                        raise
                    result["curl_exit"] = process.returncode
            # Temporary files cannot exceed the subprocess file-size limit;
            # diagnostic reads have their own stricter independent bounds.
            result["body_bytes"] = body_path.stat().st_size
            if result["body_bytes"] > expected["bytes"]: raise ValueError("public response exceeds accepted body size")
            raw = body_path.read_bytes()
            result["body_sha256"] = sha256(raw).hexdigest()
            if error_path.stat().st_size > transport.MAX_STDERR or headers_path.stat().st_size > transport.MAX_HEADERS:
                raise ValueError("public response diagnostics exceed bound")
            errors, headers = error_path.read_bytes(), headers_path.read_bytes()
            result["stderr"], result["headers"] = errors.decode("latin1"), headers.decode("latin1")
            if transport.MARKER not in errors: raise ValueError("missing actual curl metadata")
            metadata = errors.rsplit(transport.MARKER, 1)[1]
            if len(metadata) > 4096: raise ValueError("oversized curl metadata")
            status, effective = metadata.rstrip(b"\n").split(b" ", 1)
            result["status"], result["effective_url"] = status.decode("ascii"), effective.decode("utf-8")
            if process.returncode != 0 or result["status"] != "200" or result["effective_url"] != url:
                raise ValueError("curl failed, redirected or returned non-200")
            statuses = transport.re.findall(r"(?m)^HTTP/(?:1\.[01]|2|3) ([0-9]{3})[^\r\n]*\r?$", result["headers"])
            if not statuses or statuses[-1] != "200": raise ValueError("actual final headers are not HTTP200")
            if transport.re.search(r"(?im)^content-encoding:\s*(?!identity\s*$)\S+", result["headers"]):
                raise ValueError("unexpected response encoding")
            if result["body_bytes"] != expected["bytes"] or result["body_sha256"] != expected["sha256"]:
                raise ValueError("public URL bytes differ from accepted staging")
            result["passed"] = True
    except (OSError, ValueError, TimeoutError, subprocess.SubprocessError) as error:
        result["failure"] = type(error).__name__ + ": " + str(error)
    result["elapsed_seconds"] = monotonic()-start
    return result


def run_batch(batch, accepted):
    start = monotonic()
    result = dict(schema="peano-v35-public-url-observation-v1", proof_authority=False,
        admission_performed=False, stage_authority=False, browser_execution_tested=False,
        accepted_stage_manifest_sha256=accepted, batch=batch, passed=False, requests=[],
        limits=dict(concurrent_requests=1, request_seconds=REQUEST_SECONDS, batch_seconds=BATCH_SECONDS))
    try:
        binding, rows = source_binding(), inventory(accepted)
        result.update(source_binding=binding, inventory=rows, inventory_path_count=len(rows),
                      inventory_sha256=transport.digest_value(rows), batches=(len(rows)+BATCH_SIZE-1)//BATCH_SIZE)
        if type(batch) is not int or not 1 <= batch <= result["batches"]: raise ValueError("invalid public URL batch")
        chosen = rows[(batch-1)*BATCH_SIZE:batch*BATCH_SIZE]
        result["planned_request_count"] = len(chosen)
        for row in chosen:
            result["requests"].append(fetch_exact(row, start+BATCH_SECONDS-CLEANUP_SECONDS))
            if result["requests"][-1].get("cleanup_failed") or monotonic() >= start+BATCH_SECONDS-CLEANUP_SECONDS: break
        if rows != inventory(accepted) or binding != source_binding(): raise ValueError("public URL inputs changed")
        if monotonic()-start > BATCH_SECONDS: raise TimeoutError("public URL batch exceeded90seconds")
        result["passed"] = len(result["requests"]) == len(chosen) and all(row["passed"] for row in result["requests"])
    except (OSError, ValueError, TimeoutError, TypeError, KeyError, subprocess.SubprocessError) as error:
        result["failure"] = type(error).__name__ + ": " + str(error)
    result["elapsed_seconds"] = monotonic()-start
    result["request_count"] = len(result["requests"])
    result["successful_requests"] = sum(row["passed"] for row in result["requests"])
    result["not_completed_count"] = result.get("planned_request_count", 0)-result["request_count"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accepted-stage-manifest-sha256", required=True)
    parser.add_argument("--batch", type=int, help="observe one batch; omitted means all bounded batches")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    # Reserve the receipt before any request: an existing observation is never
    # overwritten and does not trigger a redundant round of network requests.
    with args.output.open("xb") as stream:
        def expired(*unused): raise TimeoutError("hard90second public URL deadline")
        def bounded_batch(number):
            previous = signal.signal(signal.SIGALRM, expired)
            signal.alarm(BATCH_SECONDS)
            try:
                return run_batch(number, args.accepted_stage_manifest_sha256)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, previous)
        if args.batch is not None:
            result = bounded_batch(args.batch)
        else:
            observations = [bounded_batch(1)]
            first = observations[0]
            print(json.dumps(dict(batch=1, passed=first["passed"], requests=first["request_count"])), flush=True)
            for number in range(2, first.get("batches", 1)+1):
                if any(row.get("cleanup_failed") for row in observations[-1]["requests"]): break
                observation = bounded_batch(number)
                observations.append(observation)
                print(json.dumps(dict(batch=number, passed=observation["passed"], requests=observation["request_count"])), flush=True)
            complete = (len(observations) == first.get("batches") and all(row["passed"]
                and row.get("source_binding") == first.get("source_binding")
                and row.get("inventory_sha256") == first.get("inventory_sha256") for row in observations))
            result = dict(schema="peano-v35-public-url-observations-v1", proof_authority=False,
                admission_performed=False, stage_authority=False, browser_execution_tested=False,
                accepted_stage_manifest_sha256=args.accepted_stage_manifest_sha256,
                source_binding=first.get("source_binding"), inventory_sha256=first.get("inventory_sha256"),
                inventory_path_count=first.get("inventory_path_count"),
                request_count=sum(row["request_count"] for row in observations),
                successful_requests=sum(row["successful_requests"] for row in observations),
                batch_count=len(observations), batches=observations, passed=complete)
        stream.write(json.dumps(result, sort_keys=True, indent=2).encode()+b"\n")
    print(json.dumps({key:value for key,value in result.items() if key not in ("requests", "inventory", "source_binding", "batches")}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
