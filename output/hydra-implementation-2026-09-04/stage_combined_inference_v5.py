"""Prepare or perform the selected, exclusive source04-to-source05 ordinary copy.

Default invocation only reads local sealed files and prints a deterministic
review. --stage requires that exact saved review SHA and creates one new local
attempt. It never resumes, retries, overwrites a destination, or allocates jobs.
"""
from pathlib import Path
import argparse
import ast
import base64
import hashlib
import json
import os
import re
import selectors
import shlex
import stat
import subprocess
import time

HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "combined-source-bundle-05"
PARENT = HERE / "combined-source-bundle-04"
OUT = HERE / "combined-inference-transfer-05"
CAMPAIGN = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904"
OLD = CAMPAIGN + "/bundles/combined-source-04"
DESTINATION = CAMPAIGN + "/bundles/combined-source-05"
BORROW = CAMPAIGN + "/bundles/source-data-07/source"
CHANGED = "output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py"
CONTROLLER = {"bytes":53996,"sha256":"cb5ba7840f85c00bf54953bddf5bb168414a0e6e84c9b41369da63b315e195be"}
TEMPLATE_SHA = "fd5cdbf32c042111064dd70c351e78353771edd99498ad55e209b469e243c42c"
SEAL_SHA = "5a8c150f9c0f743c46411529a7a879d1836f163682bf744eadd1e7952ed00dff"
ACTUAL_SHA = "de059f1aebd34e17fba2ff741b32b9dabf4cf4976af12c5148a9dd6279e594e6"
GATE_SHA = "89db1443dd2021627857cf0842727e75e9d8865cd1bafd23fabaab1516257bff"
MANIFEST_CONTENT_SHA = "37958389121a4f6bca22d1b4161f004b66a604455130d57a1d2fa665dc4eea99"
PARENT_SHA = "4beeb386a118229b4e3fa9b751d7a4a560853252ab3103cff661a48dc2eb9f0e"
PARENT_CONTENT_SHA = "aa001fceb6eaefcf3073287f8cb8a8efacffc245fe524759ad95a0d34571c9dd"
METADATA = {
    "manifest.json":{"bytes":267734,"sha256":"bac311e7e1c6283f762bfc278a64993383d090b23f3350f379454ba4ed41b9fd"},
    "paired-source-pins.json":{"bytes":126170,"sha256":"488b332e353e0f2d24ac71b19e5c2d3369641aeb0da3605fa5aa25afe43e70c1"},
    "teacher-source-pins.json":{"bytes":108200,"sha256":"e76da7607ea7be7681c30a5583bfb71c998aab7660754e28cb0c4cb61f5b3d7a"},
    "student-source-pins.json":{"bytes":101298,"sha256":"8e55a8f20c5aaf8893d5850c008d0a54408cac9600d2827de4b6eeb95f2c887c"},
    "teacher-paired-source-pins.json":{"bytes":126761,"sha256":"d184338a35b8aebde03a5edad16995038717502d4d84924da7f4750e36247ce9"},
}
SSH = ['/usr/bin/ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15',
       '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','-o','ForwardAgent=no',
       '-o','ClearAllForwardings=yes','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no',
       '-o','ControlMaster=no','-o','ControlPath=none','--','plgnasqret@helios.cyfronet.pl']


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def descriptor(raw):
    return {"bytes":len(raw),"sha256":digest(raw)}


def stamp(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def read_local(path, maximum=1024**2):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum,
            "Missing, linked or oversized local source input")
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,"rb") as stream:
        require(stamp(os.fstat(stream.fileno())) == stamp(before),"Local input identity changed")
        raw = stream.read(maximum+1)
        require(stamp(os.fstat(stream.fileno())) == stamp(before),"Local input changed during read")
    require(len(raw) == before.st_size and stamp(path.lstat()) == stamp(before),"Local input path/bytes changed")
    return raw


def prepared():
    seal_raw,actual_raw,gate_raw = (read_local(BUNDLE/name) for name in
                                   ("SEALED.json","actual-completion.json","gate-completion.json"))
    require(digest(seal_raw) == SEAL_SHA and digest(actual_raw) == ACTUAL_SHA and digest(gate_raw) == GATE_SHA,
            "Actual sealed source05 build evidence changed")
    seal,actual,gate = (json.loads(raw) for raw in (seal_raw,actual_raw,gate_raw))
    require(seal["status"] == "SEALED_FILE_ONLY_GATE_PASSED" and seal["source_file_count"] == 1345
            and actual["actual_exit_code"] == 0 and actual["completion_chunk"] == "d0bcab"
            and gate["passed"] is True and gate["runtime_imports"] == gate["native_runs"] == gate["model_calls"] == 0,
            "Source05 lacks its genuine successful file-only build")
    for name,expected in seal["files"].items():
        require(descriptor(read_local(BUNDLE/name,16*1024**2)) == expected,"Sealed bundle evidence changed: "+name)
    admission_raw = read_local(HERE/"p6-source04-repair-02/ACTUAL_ADMISSION.json")
    require(descriptor(admission_raw) == {"bytes":1111,"sha256":"9629ee03e999fa876af4b07b5d22fff8d5b3fea9ea4811d709b0e7e95f4f264e"},
            "Source04 actual admission changed")
    admission = json.loads(admission_raw)
    require(admission["passed"] is True and admission["admission"]["source"] == OLD+"/source"
            and admission["admission"]["manifest_sha256"] == PARENT_SHA
            and admission["admission"]["original_stage_exit_code"] == 255,
            "The separately admitted source04 repair is required; old stage remains failed")
    metadata = {name:read_local(BUNDLE/name) for name in METADATA}
    require(all(descriptor(raw) == METADATA[name] for name,raw in metadata.items()),"Exact raw metadata changed")
    manifest = json.loads(metadata["manifest.json"])
    require(digest(canonical(manifest)) == MANIFEST_CONTENT_SHA and manifest["file_count"] == 1345
            and manifest["expanded_bytes"] == 112221252 and manifest["files"][CHANGED] == CONTROLLER
            and manifest["archive_sha256"] == "a77cc75f002660b4f721f8d1e44c38f8249b65575948c2b1de40ad2d9d0fef53",
            "Fixed source05 identity differs")
    parent_raw = read_local(PARENT/"manifest.json")
    require(digest(parent_raw) == PARENT_SHA and digest(canonical(json.loads(parent_raw))) == PARENT_CONTENT_SHA,
            "Exact original parent manifest changed")
    parent = json.loads(parent_raw)
    additions = json.loads(read_local(BUNDLE/"added-files.json"))
    changes = json.loads(read_local(BUNDLE/"changed-files.json"))
    require(changes == manifest["changed_files"] and set(changes) == {CHANGED}
            and additions == manifest["added_files"] and len(additions) == 20
            and sum(item["bytes"] for item in additions.values()) == 128574
            and set(manifest["files"]) == set(parent["files"]) | set(additions)
            and not set(parent["files"]) & set(additions)
            and {name for name in parent["files"] if parent["files"][name] != manifest["files"][name]} == {CHANGED},
            "Changes exceed the selected controller and baseline closure")
    for kind,pin in manifest["source_maps"].items():
        name = kind+"-source-pins.json"
        raw,scope = metadata[name],json.loads(metadata[name])
        require(descriptor(raw) == {key:pin[key] for key in ("bytes","sha256")}
                and len(scope) == pin["files"] and digest(canonical(scope)) == pin["content_sha256"],
                "Source-map binding differs")
        require(all((manifest["files"][key]["sha256"] if kind == "teacher" else manifest["files"][key]) == value
                    for key,value in scope.items()),"Source-map entry differs")
        if kind != "paired":
            require(read_local(PARENT/name) == raw,"Unrelated map changed")
    payloads = {name:metadata[name] for name in ("manifest.json","paired-source-pins.json")}
    payloads["source/"+CHANGED] = read_local(BUNDLE/"source"/CHANGED)
    require(descriptor(payloads["source/"+CHANGED]) == CONTROLLER
            and sum(map(len,payloads.values())) == 447900,"Exact three upload payloads differ")
    request = {"schema":"hydra-combined-inference-source-copy-request-v5",
               "authority":"HYDRA_EXPERIMENT_AUTHORITY.md","automatic_retry":False,
               "payloads":{name:base64.b64encode(raw).decode("ascii") for name,raw in payloads.items()}}
    wire = canonical(request)
    require(len(wire) <= 2*1024**2,"Copy input exceeds its bound")
    bindings = {"request_sha256":digest(wire),"payloads":{n:descriptor(v) for n,v in payloads.items()},
                "metadata":METADATA,"manifest_content_sha256":MANIFEST_CONTENT_SHA}
    template = read_local(BUNDLE/"remote_copy.py",65536)
    require(digest(template) == TEMPLATE_SHA and template.count(b"BINDINGS = None\n") == 1,
            "Reviewed copier template changed")
    code = template.replace(b"BINDINGS = None\n",("BINDINGS = "+repr(bindings)+"\n").encode(),1)
    ast.parse(code,feature_version=(3,6))
    require(len(code) <= 65536,"Generated copy script exceeds its bound")
    review = {"schema":"hydra-combined-inference-source-copy-review-v5",
        "payload_pins":bindings["payloads"],"raw_payload_bytes":447900,"wire_payload_bytes":len(wire),
        "wire_payload_sha256":digest(wire),"remote_script_sha256":digest(code),"remote_script_bytes":len(code),
        "remote_template_sha256":TEMPLATE_SHA,"source_files_copied":1345,"unchanged_source_files":1324,
        "changed_source_files":[CHANGED],"added_source_files":sorted(additions),
        "borrowed_source_files":20,"borrowed_source_bytes":128574,
        "copied_unchanged_metadata_files":["student-source-pins.json","teacher-paired-source-pins.json","teacher-source-pins.json"],
        "remote_parent":OLD,"remote_borrowed_source":BORROW,"remote_destination":DESTINATION,
        "parent_local_manifest_sha256":PARENT_SHA,"parent_remote_manifest_sha256":PARENT_SHA,
        "parent_manifest_content_sha256":PARENT_CONTENT_SHA,"manifest_raw_bytes_preserved":True,
        "manifest_sha256":METADATA["manifest.json"]["sha256"],"manifest_content_sha256":MANIFEST_CONTENT_SHA,
        "parent_actual_admission_sha256":digest(admission_raw),"archive_uploaded":False,
        "bounds":{"wire_bytes":2*1024**2,"expanded_bytes":112221252,
                  "remote_cpu_soft_seconds":60,"remote_cpu_hard_seconds":75,"remote_wall_seconds":240,
                  "remote_address_space_bytes":512*1024**2,"ssh_wall_seconds":270,"ssh_cleanup_seconds":5,
                  "maximum_stdout_bytes":65536,"maximum_stderr_bytes":65536,"quota_query_wall_seconds":10,
                  "quota_output_bytes":16384,"maximum_open_directories":192,"maximum_cached_source_bytes":128*1024**2},
        "source_directories":65,"inode_quota_required_with_reserve":1674,
        "teacher_baseline_file_closure":122,"teacher_admission_executed":False,
        "application_executions":0,"gpu_allocations":0,"automatic_retry":False}
    return review,code,wire


# The reviewed repair02 transport body is inserted below without changes except
# the selected 150-to-270-second outer maintenance deadline.


def run_transport(argv, wire):
    """Bound capture while pumping stdin; abort only this owned SSH process."""
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    poller = selectors.DefaultSelector()
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    written = 0
    deadline = time.monotonic() + 270
    timed_out = False
    exceeded = False
    io_error = None
    for name, stream, event in [('stdin', process.stdin, selectors.EVENT_WRITE),
                                ('stdout', process.stdout, selectors.EVENT_READ),
                                ('stderr', process.stderr, selectors.EVENT_READ)]:
        os.set_blocking(stream.fileno(), False)
        poller.register(stream, event, name)
    try:
        while poller.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            for key, _ in poller.select(min(remaining, 0.25)):
                name, stream = key.data, key.fileobj
                if name == 'stdin':
                    try:
                        written += os.write(stream.fileno(), wire[written:written + 65536])
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        poller.unregister(stream)
                        stream.close()
                        continue
                    if written == len(wire):
                        poller.unregister(stream)
                        stream.close()
                else:
                    try:
                        chunk = os.read(stream.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        poller.unregister(stream)
                        stream.close()
                        continue
                    available = 65536 - len(buffers[name])
                    buffers[name].extend(chunk[:available])
                    if len(chunk) > available:
                        exceeded = True
                        break
            if exceeded:
                break
    except OSError as error:
        io_error = type(error).__name__
    finally:
        if timed_out or exceeded or io_error:
            if process.poll() is None:
                process.kill()
        for key in list(poller.get_map().values()):
            poller.unregister(key.fileobj)
            key.fileobj.close()
        poller.close()
    try:
        exit_code = process.wait(timeout=max(0.01, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        exit_code = process.wait(timeout=5)
    return {'actual_ssh_exit_code': exit_code, 'outer_timeout': timed_out,
            'output_limit_exceeded': exceeded, 'io_error': io_error,
            'capture_complete': not (timed_out or exceeded or io_error),
            'stdin_bytes_written': written, 'stdin_bytes_expected': len(wire)}, bytes(buffers['stdout']), bytes(buffers['stderr'])



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",action="store_true",help="One selected remote copy; default is local metadata only")
    parser.add_argument("--review-sha256",help="Required raw SHA of the saved, exact COPY_REVIEW.json for --stage")
    args = parser.parse_args()
    review,code,wire = prepared()
    if not args.stage:
        print(json.dumps(review,sort_keys=True),flush=True)
        return 0
    require(type(args.review_sha256) is str and re.fullmatch("[0-9a-f]{64}",args.review_sha256),
            "The exact local copy review SHA is required")
    review_raw = read_local(BUNDLE/"COPY_REVIEW.json",65536)
    require(digest(review_raw) == args.review_sha256 and json.loads(review_raw) == review,
            "Selected copy review or generated script/payload binding changed")
    OUT.mkdir(exist_ok=False)
    for name,value in (("review.json",review_raw),("remote-script.py",code),
                       ("intent.json",canonical({"schema":"hydra-source05-stage-intent-v1",
                        "review_sha256":args.review_sha256,"remote_script_sha256":digest(code),
                        "wire_payload_sha256":digest(wire),"remote_destination":DESTINATION,
                        "automatic_retry":False})+b"\n")):
        with (OUT/name).open("xb") as stream:
            stream.write(value)
    began = time.monotonic()
    transport,stdout,stderr = run_transport(
        SSH+["/usr/bin/python3 -I -B -c "+shlex.quote(code.decode("utf-8"))],wire)
    for name,value in (("stdout.json",stdout),("stderr.txt",stderr)):
        with (OUT/name).open("xb") as stream:
            stream.write(value)
    receipt = {"schema":"hydra-combined-inference-source-stage-actual-completion-v5",
        **transport,"elapsed_seconds":time.monotonic()-began,"review":review,
        "review_sha256":args.review_sha256,"stdout_sha256":digest(stdout),"stderr_sha256":digest(stderr),
        "stdout":descriptor(stdout),"stderr":descriptor(stderr),"remote_copy_outcome":"unadmitted_until_receipt_validation",
        "gpu_allocations":0,"model_calls":0,"native_runs":0,"automatic_retry":False}
    with (OUT/"actual-completion.json").open("xb") as stream:
        stream.write(canonical(receipt)+b"\n")
    print(json.dumps(receipt,sort_keys=True),flush=True)
    if not transport["capture_complete"] or transport["stdin_bytes_written"] != len(wire):
        return 1
    return transport["actual_ssh_exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
