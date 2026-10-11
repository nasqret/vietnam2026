"""Reporting a supervision failure must not discard records or assert success."""
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

import validate_sqrt2_power_wave as validation


def _fixture(tmp_path,monkeypatch,*,failure_on=None,invalid_record_on=None):
    # This known filename exercises separate isolated batches without spawning
    # any worker. Fake process records are test fixtures, never real evidence.
    name="test_sqrt2_power_exp_truncation.py"
    (tmp_path/name).write_text("def test_one(): pass\ndef test_two(): pass\ndef test_three(): pass\n")
    actual=validation.runtime();calls=[];validated=[]
    def run(command,*,cwd,limits):
        calls.append((command,cwd,limits))
        if len(calls)==failure_on:
            raise actual.ReviewRuntimeError("owned process-group accounting unavailable")
        return dict(reason="exited",returncode=0,output_truncated=False,stdout="fixture only",resources={},ordinal=len(calls))
    def check(record,**kwargs):
        if record["ordinal"]==invalid_record_on:
            raise actual.ReviewRuntimeError("invalid resource receipt")
        validated.append(record)
    fake=SimpleNamespace(ProcessLimits=actual.ProcessLimits,ReviewRuntimeError=actual.ReviewRuntimeError,
        run_bounded=run,validate_process_record=check,hash_file=actual.hash_file)
    monkeypatch.setattr(validation,"ROOT",tmp_path)
    monkeypatch.setattr(validation,"runtime",lambda:fake)
    return name,calls,validated


def test_supervision_failure_preserves_only_preceding_validated_records(tmp_path,monkeypatch):
    name,calls,validated=_fixture(tmp_path,monkeypatch,failure_on=2)
    output=tmp_path/"interrupted.json"
    assert validation.validate(output,[name])=="failed_or_incomplete"
    report=json.loads(output.read_bytes())
    assert report["requested_batches"]==3 and report["completed_batches"]==1
    assert report["processes"]==validated and len(calls)==2
    assert report["interruption"]["batch"]==[name+"::test_two"]
    assert report["interruption"]["exception"]=="ReviewRuntimeError"
    assert report["max_workers"]==1 and report["IR_parents_closed"]==0
    for _,_,limits in calls:
        assert (limits.cpu_seconds,limits.wall_seconds,limits.rss_bytes,limits.output_bytes)==(25,35,512*1024**2,1024**2)


def test_first_failure_never_creates_a_successful_or_invented_process(tmp_path,monkeypatch):
    name,calls,validated=_fixture(tmp_path,monkeypatch,failure_on=1)
    output=tmp_path/"first.json"
    assert validation.validate(output,[name])=="failed_or_incomplete"
    report=json.loads(output.read_bytes())
    assert report["processes"]==validated==[] and report["completed_batches"]==0
    assert len(calls)==1 and report["interruption"]["reason"]=="supervision_failed"


def test_invalid_resource_record_is_excluded_and_stops_the_batch(tmp_path,monkeypatch):
    name,calls,validated=_fixture(tmp_path,monkeypatch,invalid_record_on=2)
    output=tmp_path/"invalid.json"
    assert validation.validate(output,[name])=="failed_or_incomplete"
    report=json.loads(output.read_bytes())
    assert len(calls)==2 and report["processes"]==validated and len(validated)==1
    assert report["interruption"]["message"]=="invalid resource receipt"


def test_complete_success_and_immutable_report_source_binding(tmp_path,monkeypatch):
    name,calls,validated=_fixture(tmp_path,monkeypatch)
    output=tmp_path/"complete.json"
    assert validation.validate(output,[name])=="passed"
    raw=output.read_bytes();report=json.loads(raw)
    assert report["completed_batches"]==report["requested_batches"]==3
    assert report["processes"]==validated and len(calls)==3 and report["interruption"] is None
    assert report["validator_sha256"]==sha256(validation.Path(validation.__file__).read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        validation.validate(output,[name])
    assert output.read_bytes()==raw
