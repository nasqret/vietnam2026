"""Prepare or perform the selected, exclusive source06-to-source07 ordinary copy.

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
BUNDLE = HERE / "combined-source-bundle-07"
PARENT = HERE / "combined-source-bundle-06"
OUT = HERE / "combined-inference-transfer-07"
CAMPAIGN = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904"
OLD = CAMPAIGN + "/bundles/combined-source-06"
DESTINATION = CAMPAIGN + "/bundles/combined-source-07"
CHANGED = "output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py"
CONTROLLER = {'bytes': 59474, 'sha256': '58691d59232f2cc8b22a0f55422366572c647de15459f8c6e7460b4d5efe145b'}
TEMPLATE_SHA = 'b9f754bee4ce9b9621ec00c50c13e434b67bca2fa3683652c0dbb4c4f20eb70b'
SEAL_SHA = 'efc69cf7f6f68d5ba25516fffd8244e02a3b1033f89ef4deff072af8f576a1c7'
ACTUAL_SHA = '24ad6ba6ec0e0ce2c96cb035d796e9aadcfbc1426cd16622fc9afccb75e69efb'
GATE_SHA = '9f972e2bc92b11cd42d9404ccc17519411189e5b7c321d523cb35d202c279c10'
MANIFEST_CONTENT_SHA = 'b1ef048f6122a00637256427d963a5df53a8b456b75046d82198295ed01b5342'
PARENT_SHA = 'd1b02961a6034d2f9edcd97974713cfef37cd64787664d1b2c3672a8aa309eeb'
PARENT_CONTENT_SHA = 'bbde2946041dbe7ec58a69ee9fe5a1f58c59f1a31dc1566d8b01534c43a083a5'
METADATA = {'manifest.json': {'bytes': 257450, 'sha256': '220759fb24af3c3fac647e4fbdafe6a9a7437a068a8b668b7638905510b1e641'}, 'paired-source-pins.json': {'bytes': 126170, 'sha256': '4c61a59468f3efbb48098afebe0bd83a2f7975127ef598d9ff4d99da658314c6'}, 'teacher-source-pins.json': {'bytes': 108200, 'sha256': 'e76da7607ea7be7681c30a5583bfb71c998aab7660754e28cb0c4cb61f5b3d7a'}, 'student-source-pins.json': {'bytes': 101298, 'sha256': '8e55a8f20c5aaf8893d5850c008d0a54408cac9600d2827de4b6eeb95f2c887c'}, 'teacher-paired-source-pins.json': {'bytes': 126761, 'sha256': 'd184338a35b8aebde03a5edad16995038717502d4d84924da7f4750e36247ce9'}}

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
            "Actual sealed source07 build evidence changed")
    seal,actual,gate = (json.loads(raw) for raw in (seal_raw,actual_raw,gate_raw))
    require(seal["status"] == "SEALED_FILE_ONLY_GATE_PASSED" and seal["source_file_count"] == 1345
            and actual["actual_exit_code"] == 0 and actual["completion_chunk"] == "cc12c6"
            and gate["passed"] is True and gate["runtime_imports"] == gate["native_runs"] == gate["model_calls"] == 0,
            "Source07 lacks its genuine successful file-only build")
    for name,expected in seal["files"].items():
        require(descriptor(read_local(BUNDLE/name,16*1024**2)) == expected,"Sealed bundle evidence changed: "+name)
    admission_raw = read_local(HERE/"paired-launchers-v12/bindings.json")
    require(descriptor(admission_raw) == {"bytes":4358,"sha256":"b850b17e651159cb925dadc4b51333e16db4136bfddc33912d5f7fb32c259665"},
            "Source06 actual admission changed")
    admission = json.loads(admission_raw)
    gate_actual_raw = read_local(HERE/"paired-launchers-v12/bindings.actual.json")
    require(descriptor(gate_actual_raw) == {"bytes":952,"sha256":"7ea58042bf6f0ae736ccec9cff6bce9b13e1180f1e809bf8d7ce382233439904"},
            "The source06 admission lacks its genuine tool completion")
    gate_actual = json.loads(gate_actual_raw)
    require(admission["passed"] is True and admission["actual_source06_transfer_admitted"] is True
            and gate_actual["actual_exit_code"] == 0 and gate_actual["completion_chunk"] == "ae695c"
            and gate_actual["actual_source06_metadata_admission"] is True
            and {key:gate_actual["result"][key] for key in ("bytes","sha256")} == descriptor(admission_raw),
            "The genuinely admitted source06 ordinary copy is required")
    parent_evidence = {}
    for key in ("response","transport","actual_tool_completion"):
        expected = admission["actual_source06_transfer"][key]
        value = read_local(HERE.parents[1]/expected["path"])
        require(descriptor(value) == {name:expected[name] for name in ("bytes","sha256")},
                "Underlying admitted source06 evidence changed")
        parent_evidence[key] = json.loads(value)
    response,transport,actual_parent = (parent_evidence[key] for key in ("response","transport","actual_tool_completion"))
    require(response["completed"] is True and response["source"] == OLD+"/source"
            and response["manifest_sha256"] == PARENT_SHA
            and response["verified_files"] == 1345 and response["verified_bytes"] == 112222012
            and response["baseline_closure_verified"] is True
            and actual_parent["actual_exit_code"] == 0 and actual_parent["completion_chunk"] == "80afa7"
            and actual_parent["source_copy_completed"] is True
            and transport["actual_ssh_exit_code"] == 0 and transport["capture_complete"] is True
            and transport["outer_timeout"] is False and transport["output_limit_exceeded"] is False
            and transport["io_error"] is None
            and transport["stdin_bytes_written"] == transport["stdin_bytes_expected"]
            and transport["stdout_sha256"] == admission["actual_source06_transfer"]["response"]["sha256"],
            "Parent transfer is not an unchanged complete actual copy")
    metadata = {name:read_local(BUNDLE/name) for name in METADATA}
    require(all(descriptor(raw) == METADATA[name] for name,raw in metadata.items()),"Exact raw metadata changed")
    manifest = json.loads(metadata["manifest.json"])
    files = manifest["files"]
    expanded_bytes = sum(item["bytes"] for item in files.values())
    require(digest(canonical(manifest)) == MANIFEST_CONTENT_SHA and manifest["file_count"] == len(files) == 1345
            and manifest["expanded_bytes"] == expanded_bytes and files[CHANGED] == CONTROLLER
            and manifest["archive_sha256"] == "3b67abb3e34a1e84d2dc5abed21b6a68c4db7ebe762ef243835f9970f45a5b4e",
            "Fixed source07 identity differs")
    parent_raw = read_local(PARENT/"manifest.json")
    require(digest(parent_raw) == PARENT_SHA and digest(canonical(json.loads(parent_raw))) == PARENT_CONTENT_SHA,
            "Exact original parent manifest changed")
    parent = json.loads(parent_raw)
    additions = json.loads(read_local(BUNDLE/"added-files.json"))
    changes = json.loads(read_local(BUNDLE/"changed-files.json"))
    require(changes == manifest["changed_files"] and set(changes) == {CHANGED}
            and additions == manifest["added_files"] == {} and manifest["added_file_count"] == manifest["added_bytes"] == 0
            and set(files) == set(parent["files"])
            and {name for name in parent["files"] if parent["files"][name] != files[name]} == {CHANGED}
            and expanded_bytes == parent["expanded_bytes"] - parent["files"][CHANGED]["bytes"] + CONTROLLER["bytes"],
            "Changes exceed the selected single controller; no additions or borrowing are allowed")
    closure = json.loads(read_local(BUNDLE/"baseline-closure.json"))
    require(closure == manifest["teacher_dependency_closure"] and closure["files"] == 122
            and closure["all_initial_working_bytes_match"] is True and closure["added_files"] == closure["added_bytes"] == 0,
            "Previously completed teacher baseline closure differs")
    for kind,pin in manifest["source_maps"].items():
        name = kind+"-source-pins.json"
        raw,scope = metadata[name],json.loads(metadata[name])
        require(descriptor(raw) == {key:pin[key] for key in ("bytes","sha256")}
                and len(scope) == pin["files"] and digest(canonical(scope)) == pin["content_sha256"],
                "Source-map binding differs")
        require(all((files[key]["sha256"] if kind == "teacher" else files[key]) == value
                    for key,value in scope.items()),"Source-map entry differs")
        if kind != "paired":
            require(read_local(PARENT/name) == raw,"Unrelated map changed")
        else:
            old_scope = json.loads(read_local(PARENT/name))
            require(set(old_scope) == set(scope) and {key for key in scope if scope[key] != old_scope[key]} == {CHANGED},
                    "Paired map changes exceed the single controller")
    payloads = {name:metadata[name] for name in ("manifest.json","paired-source-pins.json")}
    payloads["source/"+CHANGED] = read_local(BUNDLE/"source"/CHANGED)
    expected_payload_bytes = CONTROLLER["bytes"] + sum(METADATA[name]["bytes"] for name in ("manifest.json","paired-source-pins.json"))
    require(descriptor(payloads["source/"+CHANGED]) == CONTROLLER
            and sum(map(len,payloads.values())) == expected_payload_bytes,"Exact three upload payloads differ")
    request = {"schema":"hydra-combined-inference-source-copy-request-v7",
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
    source_dirs = {""} | {parent.as_posix() for name in files for parent in Path(name).parents if parent.as_posix() != "."}
    inode_reserve = len(files) + len(source_dirs) + 1 + len(metadata) + 2 + 256
    review = {"schema":"hydra-combined-inference-source-copy-review-v7",
        "payload_pins":bindings["payloads"],"raw_payload_bytes":expected_payload_bytes,"wire_payload_bytes":len(wire),
        "wire_payload_sha256":digest(wire),"remote_script_sha256":digest(code),"remote_script_bytes":len(code),
        "remote_template_sha256":TEMPLATE_SHA,"source_files_copied":len(files),"unchanged_source_files":len(files)-1,
        "changed_source_files":[CHANGED],"added_source_files":[],
        "borrowed_source_files":0,"borrowed_source_bytes":0,
        "copied_unchanged_metadata_files":["student-source-pins.json","teacher-paired-source-pins.json","teacher-source-pins.json"],
        "remote_parent":OLD,"remote_borrowed_source":None,"remote_destination":DESTINATION,
        "parent_local_manifest_sha256":PARENT_SHA,"parent_remote_manifest_sha256":PARENT_SHA,
        "parent_manifest_content_sha256":PARENT_CONTENT_SHA,"manifest_raw_bytes_preserved":True,
        "manifest_sha256":METADATA["manifest.json"]["sha256"],"manifest_content_sha256":MANIFEST_CONTENT_SHA,
        "parent_actual_admission_sha256":digest(admission_raw),"archive_uploaded":False,
        "bounds":{"wire_bytes":2*1024**2,"expanded_bytes":expanded_bytes,
                  "remote_cpu_soft_seconds":60,"remote_cpu_hard_seconds":75,"remote_wall_seconds":240,
                  "remote_address_space_bytes":512*1024**2,"ssh_wall_seconds":270,"ssh_cleanup_seconds":5,
                  "maximum_stdout_bytes":65536,"maximum_stderr_bytes":65536,"quota_query_wall_seconds":10,
                  "quota_output_bytes":16384,"maximum_open_directories":192,"maximum_cached_source_bytes":128*1024**2},
        "source_directories":len(source_dirs),"inode_quota_required_with_reserve":inode_reserve,
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
                       ("intent.json",canonical({"schema":"hydra-source07-stage-intent-v1",
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
    receipt = {"schema":"hydra-combined-inference-source-stage-actual-completion-v7",
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
