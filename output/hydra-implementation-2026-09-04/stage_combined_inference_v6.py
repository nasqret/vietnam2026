"""Prepare or perform the selected, exclusive source05-to-source06 ordinary copy.

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
BUNDLE = HERE / "combined-source-bundle-06"
PARENT = HERE / "combined-source-bundle-05"
OUT = HERE / "combined-inference-transfer-06"
CAMPAIGN = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904"
OLD = CAMPAIGN + "/bundles/combined-source-05"
DESTINATION = CAMPAIGN + "/bundles/combined-source-06"
CHANGED = "output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py"
CONTROLLER = {'bytes': 54756, 'sha256': 'caff33d11918bad304ddf0a04021550a6d686d254e604342190df094958ce482'}
TEMPLATE_SHA = '230d550894f03aee9154a18f289ec89fd70a41a56cd27fd781ba85ff1cc360a2'
SEAL_SHA = '55f050438cf36f607bc43cba6ae34eeda41ecc6b6b0f3e3b898519859053ed07'
ACTUAL_SHA = '8840b77b0443bf0ef424c08304f6ba6741d49abd48abc4cc82613c3d8c973cbf'
GATE_SHA = 'dbfe9e8df07ba567a38874842ca46d593dfd67a02789b79c3e68465602e387d6'
MANIFEST_CONTENT_SHA = 'bbde2946041dbe7ec58a69ee9fe5a1f58c59f1a31dc1566d8b01534c43a083a5'
PARENT_SHA = 'bac311e7e1c6283f762bfc278a64993383d090b23f3350f379454ba4ed41b9fd'
PARENT_CONTENT_SHA = '37958389121a4f6bca22d1b4161f004b66a604455130d57a1d2fa665dc4eea99'
METADATA = {'manifest.json': {'bytes': 257445, 'sha256': 'd1b02961a6034d2f9edcd97974713cfef37cd64787664d1b2c3672a8aa309eeb'}, 'paired-source-pins.json': {'bytes': 126170, 'sha256': '772b9cb2f228c07c3a5fb4810e376fde990beb9466c6252cf1198ea30594604e'}, 'teacher-source-pins.json': {'bytes': 108200, 'sha256': 'e76da7607ea7be7681c30a5583bfb71c998aab7660754e28cb0c4cb61f5b3d7a'}, 'student-source-pins.json': {'bytes': 101298, 'sha256': '8e55a8f20c5aaf8893d5850c008d0a54408cac9600d2827de4b6eeb95f2c887c'}, 'teacher-paired-source-pins.json': {'bytes': 126761, 'sha256': 'd184338a35b8aebde03a5edad16995038717502d4d84924da7f4750e36247ce9'}}

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
            "Actual sealed source06 build evidence changed")
    seal,actual,gate = (json.loads(raw) for raw in (seal_raw,actual_raw,gate_raw))
    require(seal["status"] == "SEALED_FILE_ONLY_GATE_PASSED" and seal["source_file_count"] == 1345
            and actual["actual_exit_code"] == 0 and actual["completion_chunk"] == "336482"
            and gate["passed"] is True and gate["runtime_imports"] == gate["native_runs"] == gate["model_calls"] == 0,
            "Source06 lacks its genuine successful file-only build")
    for name,expected in seal["files"].items():
        require(descriptor(read_local(BUNDLE/name,16*1024**2)) == expected,"Sealed bundle evidence changed: "+name)
    admission_raw = read_local(HERE/"paired-launchers-v10/copy-admission-01/result.json")
    require(descriptor(admission_raw) == {"bytes":1589,"sha256":"23c42f8352b88b775d71d077c5206b4acc30a696d327e3369855c58b49e4f995"},
            "Source05 actual admission changed")
    admission = json.loads(admission_raw)
    require(admission["passed"] is True and admission["error"] is None
            and admission["inputs"]["source_manifest"]["sha256"] == PARENT_SHA
            and admission["verified_files"] == 1345 and admission["baseline_closure_files"] == 122,
            "The genuinely admitted source05 ordinary copy is required")
    parent_evidence = {}
    for key in ("actual_copy_response","actual_copy_transport"):
        expected = admission["inputs"][key]
        value = read_local(HERE.parents[1]/expected["path"])
        require(descriptor(value) == {name:expected[name] for name in ("bytes","sha256")},
                "Underlying admitted source05 evidence changed")
        parent_evidence[key] = json.loads(value)
    response,transport = parent_evidence["actual_copy_response"],parent_evidence["actual_copy_transport"]
    require(response["completed"] is True and response["source"] == OLD+"/source"
            and response["manifest_sha256"] == PARENT_SHA
            and response["verified_files"] == admission["verified_files"]
            and response["verified_bytes"] == admission["verified_bytes"]
            and transport["actual_ssh_exit_code"] == 0 and transport["capture_complete"] is True
            and transport["outer_timeout"] is False and transport["output_limit_exceeded"] is False
            and transport["io_error"] is None
            and transport["stdin_bytes_written"] == transport["stdin_bytes_expected"]
            and transport["stdout_sha256"] == admission["inputs"]["actual_copy_response"]["sha256"],
            "Parent transfer is not an unchanged complete actual copy")
    metadata = {name:read_local(BUNDLE/name) for name in METADATA}
    require(all(descriptor(raw) == METADATA[name] for name,raw in metadata.items()),"Exact raw metadata changed")
    manifest = json.loads(metadata["manifest.json"])
    files = manifest["files"]
    expanded_bytes = sum(item["bytes"] for item in files.values())
    require(digest(canonical(manifest)) == MANIFEST_CONTENT_SHA and manifest["file_count"] == len(files) == 1345
            and manifest["expanded_bytes"] == expanded_bytes and files[CHANGED] == CONTROLLER
            and manifest["archive_sha256"] == "d03ac9cc1ccece1e46d8cd23c9d8b5288096c94d6366ff80c09ec0fd5caf540a",
            "Fixed source06 identity differs")
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
    request = {"schema":"hydra-combined-inference-source-copy-request-v6",
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
    review = {"schema":"hydra-combined-inference-source-copy-review-v6",
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
                       ("intent.json",canonical({"schema":"hydra-source06-stage-intent-v1",
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
    receipt = {"schema":"hydra-combined-inference-source-stage-actual-completion-v6",
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
