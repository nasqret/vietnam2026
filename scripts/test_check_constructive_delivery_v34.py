"""Pure local delivery guards. Fake HTTP transport never invokes curl/network."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic
from threading import Event
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_constructive_delivery_v34 as check


@pytest.mark.parametrize("bad", ["", "../a", "/a", "a/../b", "a//b", "./a", "a\\b", "a?b", "a#b", "a%2fb", "a\nb", None, 3])
def test_unsafe_path_rejected(bad):
    with pytest.raises(check.DeliveryError):
        check.relative_path(bad)


def test_actual_fixed_inventory_and_batches_without_stage_reads():
    rows = check.load_inventory()
    assert len(rows) == 230 and len({r["stage_relative_path"] for r in rows}) == 230
    assert [len(rows[i:i+16]) for i in range(0, 230, 16)] == [16] * 14 + [6]
    assert len([r for r in rows if r["purpose"] == "family_entrance"]) == 68
    assert check.WORKERS == 4 and check.REQUEST_SECONDS == 20 and check.BATCH_SECONDS == 90
    assert check.MAX_FILE == 64 * 1024 * 1024


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "wrong_route", "escape", "scope", "not_list"])
def test_inventory_rejections(mutation):
    data = check.strict_json(check.INVENTORY.read_bytes())
    if mutation == "missing": data["paths"].pop()
    elif mutation == "duplicate": data["paths"][1] = data["paths"][0]
    elif mutation == "wrong_route": data["paths"][0]["https_path"] = "/other/"
    elif mutation == "escape": data["paths"][0]["stage_relative_path"] = "../escape"
    elif mutation == "scope": data["path_count"] = 229
    else: data["paths"] = tuple(data["paths"])
    with pytest.raises(check.DeliveryError): check.validate_inventory(data)


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'])
def test_nonliteral_json_rejected(raw):
    with pytest.raises(check.DeliveryError): check.strict_json(raw)


@pytest.mark.parametrize("variant", ["valid", "oversized", "symlink", "changed"])
def test_source_bounded_reader(tmp_path,monkeypatch,variant):
    monkeypatch.setattr(check,"ROOT",tmp_path)
    path=tmp_path/"source";path.write_bytes(b"abc")
    if variant=="symlink":
        (tmp_path/"target").write_bytes(b"abc");path.unlink();path.symlink_to("target")
    if variant=="changed":
        original=check.ordinary;calls=0
        def changing(p,**kwargs):
            nonlocal calls
            if p==path:
                calls+=1
                if calls==2:path.write_bytes(b"replacement")
            return original(p,**kwargs)
        monkeypatch.setattr(check,"ordinary",changing)
    if variant=="valid":assert check.bounded_source(path)==b"abc"
    else:
        with pytest.raises(check.DeliveryError):check.bounded_source(path,maximum=1 if variant=="oversized" else 100)


def test_source_ancestor_identity_change_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(check,"ROOT",tmp_path)
    path=tmp_path/"source";path.write_bytes(b"abc")
    original=check.ordinary;calls=0
    def changed(p,**kwargs):
        nonlocal calls
        info=original(p,**kwargs)
        if p==tmp_path:
            calls+=1
            if calls>1:
                return SimpleNamespace(st_dev=info.st_dev,st_ino=info.st_ino+1,st_mode=info.st_mode,st_uid=info.st_uid)
        return info
    monkeypatch.setattr(check,"ordinary",changed)
    with pytest.raises(check.DeliveryError,match="ancestor"):
        check.bounded_source(path)


@pytest.fixture
def stage(tmp_path, monkeypatch):
    root = tmp_path / "stage"
    (root / "release-v34").mkdir(parents=True)
    payload = b"literal synthetic delivery only\n"
    (root / "index.html").write_bytes(payload)
    manifest = {"schema":"peano-lab-alpha-v34-public-delivery-v1", "delivery_metadata_only":True,
                "alpha_admission_performed":False,"stable_admission_performed":False,
                "alpha_version": "v34", "checked_use_count": 4223, "stable_count": 432,
                "current_files": {"index.html": {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}}}
    raw = json.dumps(manifest).encode()
    (root / check.MANIFEST).write_bytes(raw)
    monkeypatch.setattr(check, "STAGE", root)
    return root, sha256(raw).hexdigest(), payload


def test_exact_local_snapshot_has_no_authority(stage):
    root, digest, payload = stage
    result = check.stage_snapshot(["index.html"], digest)
    assert result["index.html"]["sha256"] == sha256(payload).hexdigest()
    assert set(result) == {check.MANIFEST, "index.html"}


def test_stage_open_never_blocks_on_fifo_replacement(stage,monkeypatch):
    root,_,_=stage
    original=check.os.open;seen=[]
    def opened(path,flags,*args,**kwargs):
        seen.append(flags)
        return original(path,flags,*args,**kwargs)
    monkeypatch.setattr(check.os,"open",opened)
    check.read_stage("index.html")
    required=check.os.O_NOFOLLOW|check.os.O_NONBLOCK|check.os.O_CLOEXEC
    assert seen and all(flags&required==required for flags in seen)


@pytest.mark.parametrize("mutation", ["wrong_manifest", "wrong_body", "missing", "linked_file", "linked_directory", "oversized", "missing_pin"])
def test_stage_rejects_mutations(stage, monkeypatch, mutation):
    root, digest, payload = stage
    if mutation == "wrong_manifest": digest = "0" * 64
    elif mutation == "wrong_body": (root / "index.html").write_bytes(b"wrong")
    elif mutation == "missing": (root / "index.html").unlink()
    elif mutation == "linked_file":
        (root / "original").write_bytes(payload)
        (root / "index.html").unlink(); (root / "index.html").symlink_to("original")
    elif mutation == "linked_directory":
        other = root.parent / "linked"; other.symlink_to(root, target_is_directory=True)
        monkeypatch.setattr(check, "STAGE", other)
    elif mutation == "oversized":
        with pytest.raises(check.DeliveryError): check.read_stage("index.html", maximum=1)
        return
    else:
        manifest=json.loads((root / check.MANIFEST).read_bytes());manifest["current_files"]={}
        raw=json.dumps(manifest).encode()
        (root / check.MANIFEST).write_bytes(raw); digest=sha256(raw).hexdigest()
    with pytest.raises((check.DeliveryError, OSError)): check.stage_snapshot(["index.html"], digest)


@pytest.mark.parametrize("key,value", [("schema","old"),("delivery_metadata_only",False),
    ("alpha_admission_performed",True),("stable_admission_performed",True),
    ("alpha_version","v33"),("checked_use_count",4092),("stable_count",433)])
def test_stage_wrong_scope_rejected_with_matching_hash(stage,key,value):
    root,_,_=stage
    data=json.loads((root/check.MANIFEST).read_bytes());data[key]=value
    raw=json.dumps(data).encode();(root/check.MANIFEST).write_bytes(raw)
    with pytest.raises(check.DeliveryError,match="scope"):
        check.stage_snapshot(["index.html"],sha256(raw).hexdigest())


def test_foreign_stage_owner_rejected(stage,monkeypatch):
    root,digest,_=stage
    monkeypatch.setattr(check.os,"getuid",lambda:root.stat().st_uid+1)
    with pytest.raises(check.DeliveryError,match="foreign-owned"):
        check.stage_snapshot(["index.html"],digest)


def test_stage_mutation_during_hash_rejected(stage,monkeypatch):
    root,_,_=stage
    ordinary=check.ordinary;calls=0
    def changed(path,**kwargs):
        nonlocal calls
        if path==root/"index.html":
            calls+=1
            if calls==2:path.write_bytes(b"changed during read")
        return ordinary(path,**kwargs)
    monkeypatch.setattr(check,"ordinary",changed)
    with pytest.raises(check.DeliveryError,match="changed"):
        check.read_stage("index.html")


def test_curl_command_strict_transport():
    cmd = check.curl_command(check.ORIGIN + "/proofs/index.html", "/dev/fd/7", 20)
    assert cmd[:2] == ["curl", "-q"]
    assert not {"-k", "--insecure", "-L", "--location", "--location-trusted"} & set(cmd)
    assert cmd[cmd.index("--proto")+1] == cmd[cmd.index("--proto-redir")+1] == "=https"
    assert cmd[cmd.index("--max-redirs")+1] == "0"
    assert "Accept-Encoding: identity" in cmd and cmd[cmd.index("--max-time")+1] == "20"


def fake_transport(monkeypatch, *, body=b"ok", status="200", effective=None,
                   headers=b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n", code=0,
                   metadata=True, error_bytes=0, sleep=0):
    real_popen = subprocess.Popen
    def start(command, **kwargs):
        assert command[0] == "curl"
        fd = kwargs["pass_fds"][0]
        tail = (check.MARKER.decode() + status + " " + (effective or command[-1]) + "\n") if metadata else ""
        program = ("import os,sys,time; time.sleep(float(sys.argv[1])); "
                   "os.write(int(sys.argv[2]),bytes.fromhex(sys.argv[3])); "
                   "os.write(1,bytes.fromhex(sys.argv[4])); "
                   "os.write(2,b'x'*int(sys.argv[5])+sys.argv[6].encode()); sys.exit(int(sys.argv[7]))")
        return real_popen([sys.executable, "-B", "-c", program, str(sleep), str(fd), headers.hex(),
                           body.hex(), str(error_bytes), tail, str(code)], **kwargs)
    monkeypatch.setattr(check.subprocess, "Popen", start)


@pytest.mark.parametrize("variant", ["success", "redirect", "code", "url", "hash", "short", "oversized",
                                    "headers", "missing_headers", "redirect_headers", "stderr", "encoding",
                                    "no_metadata", "curl_exit", "timeout"])
def test_actual_bounded_stream_transport_without_network(monkeypatch, variant):
    options = {}
    if variant == "redirect": options["status"] = "302"
    elif variant == "code": options["status"] = "404"
    elif variant == "url": options["effective"] = check.ORIGIN + "/elsewhere"
    elif variant == "hash": options["body"] = b"no"
    elif variant == "short": options["body"] = b"o"
    elif variant == "oversized": options["body"] = b"too long"
    elif variant == "headers": options["headers"] = b"x" * (check.MAX_HEADERS + 1)
    elif variant == "missing_headers": options["headers"] = b""
    elif variant == "redirect_headers": options["headers"] = b"HTTP/1.1 302 Found\r\n\r\n"
    elif variant == "stderr": options["error_bytes"] = check.MAX_STDERR + 1
    elif variant == "encoding": options["headers"] = b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\n\r\n"
    elif variant == "no_metadata": options["metadata"] = False
    elif variant == "curl_exit": options["code"] = 60
    elif variant == "timeout":
        options["sleep"] = 3; monkeypatch.setattr(check, "REQUEST_SECONDS", 0.05)
    fake_transport(monkeypatch, **options)
    result = check.fetch({"stage_relative_path":"index.html", "https_path":"/proofs/index.html"},
                         {"bytes":2,"sha256":sha256(b"ok").hexdigest()}, "a"*64, monotonic()+5)
    assert result["passed"] is (variant == "success")
    assert result["curl_exit"] is not None
    if variant == "success":
        assert result["status"] == "200" and result["body_bytes"] == 2
        assert result["body_sha256"] == sha256(b"ok").hexdigest() and result["failure"] is None
    else: assert result["failure"]
    assert len(result["stderr"].encode()) <= check.MAX_STDERR
    assert len(result["headers"].encode("latin1")) <= check.MAX_HEADERS


def test_expired_batch_launches_no_process(monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError("must not launch")
    monkeypatch.setattr(check.subprocess, "Popen", forbidden)
    result=check.fetch({"stage_relative_path":"index.html","https_path":"/proofs/index.html"},
                       {"bytes":2,"sha256":"a"*64}, "a"*64, monotonic()-1)
    assert not result["passed"] and result["curl_exit"] is None


def test_cleanup_stop_forbids_next_curl(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError("must not launch after cleanup failure")
    monkeypatch.setattr(check.subprocess,"Popen",forbidden)
    stop=Event();stop.set()
    result=check.fetch({"stage_relative_path":"index.html","https_path":"/proofs/index.html"},
                       {"bytes":2,"sha256":"a"*64},"a"*64,monotonic()+20,stop)
    assert not result["passed"] and result["curl_exit"] is None and "cleanup" in result["failure"]


@pytest.mark.parametrize("batch", [0,16,-1,True,"1",None])
def test_wrong_batch_rejected(batch):
    with pytest.raises(check.DeliveryError): check.run_batch(batch,"a"*64)


@pytest.mark.parametrize("mutation", ["none","stage","source","request"])
def test_batch_rebinds_and_records_failures_without_stage_or_network(monkeypatch, mutation):
    rows=[{"stage_relative_path":f"a{i}","https_path":f"/proofs/a{i}"} for i in range(230)]
    monkeypatch.setattr(check,"load_inventory",lambda:rows)
    counts={"stage":0,"source":0}
    def snapshot(names, digest):
        counts["stage"]+=1
        return {n:{"bytes":2,"sha256":("b" if mutation=="stage" and counts["stage"]==2 else "a")*64} for n in names}
    def binding():
        counts["source"]+=1
        return {"sha256":str(counts["source"] if mutation=="source" else 1)}
    monkeypatch.setattr(check,"stage_snapshot",snapshot)
    monkeypatch.setattr(check,"source_binding",binding)
    monkeypatch.setattr(check,"fetch",lambda row,*args:{"passed":mutation!="request","stage_relative_path":row["stage_relative_path"]})
    result=check.run_batch(15,"a"*64)
    assert result["request_count"]==6 and result["passed"] is (mutation=="none")
    assert result["proof_authority"] is result["admission_performed"] is result["stage_authority"] is False
    assert [r["stage_relative_path"] for r in result["requests"]]==[f"a{i}" for i in range(224,230)]


def test_no_alpha_imports():
    assert not any("editions_v" in name or "alpha_enrollment_v" in name for name in sys.modules)
