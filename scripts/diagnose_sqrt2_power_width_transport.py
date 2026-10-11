#!/usr/bin/env python3
"""Observe unchanged failed CV051-v2 local bodies; never produce a certificate.

External supervisor: 15 CPU / 20 wall seconds, 768 MiB RSS, 64 KiB output.
No producer or checker mutation; the exhausted candidate is not retried here.
"""
from hashlib import sha256
from pathlib import Path
import sys
import time

import sqrt2_power_power_width_transport as cv
from diagnose_sqrt2_power_convolution import _structure,_paths
from sqrt2_power_definitions import parse_named
from peano_lab.kernel import checker
from peano_lab.kernel.formulas import Imp,pretty_formula
from peano_lab.library.proof_bundle import encode_formula

PINS = {
    "scripts/sqrt2_power_power_width_transport.py":"094ca252a19faa039a708147e33ba5c9f3d842c6550f9ac8e299fa3df41055b3",
    "peano-lab/py/peano_lab/kernel/checker.py":"d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "scripts/diagnose_sqrt2_power_convolution.py":"2592bf12f09eef6e79d7495c71aa375089da6e09c2f931cfe2842e04ac7a8c9b",
}


def pins():
    result = cv.power_width_transport_source_pins()
    for name,digest in PINS.items():
        raw = (cv.ROOT/name).read_bytes()
        if len(raw)>2*1024**2 or sha256(raw).hexdigest()!=digest:
            raise ValueError("failed-input diagnostic pin changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    own = Path(__file__).resolve();raw = own.read_bytes()
    result[str(own.relative_to(cv.ROOT))] = dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
    return result


def formula_record(formula):
    if formula is None:
        return None
    raw = cv.canonical(encode_formula(formula))
    return dict(bytes=len(raw),sha256=sha256(raw).hexdigest(),pretty=pretty_formula(formula,[f"v{i}" for i in range(80)])[:1500])


def diagnose():
    started,before = time.monotonic(),pins()
    registry = cv.definition_registry()
    sources = {**cv.ENDPOINT_SOURCES,**cv.HELPER_SOURCES,"CV051":cv.NAMED_SOURCE}
    formulas = {name:parse_named(source,registry=registry) for name,source in sources.items()}
    factories = {"unit_unique":cv._unit_unique,"unit_transport":lambda s:cv._unit_transport(s,registry),
        "all_rows":lambda s:cv._all_rows(s,formulas["all_rows"],registry),"CV051":cv._root}
    results = []
    for name,deps in cv.HELPER_DEPENDENCIES.items():
        proof = cv.introduce(cv.Scope(),(),deps,factories[name])
        structure = _structure(proof)
        target = formulas[name]
        for dependency in reversed(deps):
            target = Imp(formulas[dependency],target)
        events,failed,strict = 0,[],[]
        check_code,infer_code = checker._check.__code__,checker._infer.__code__
        def profile(frame,event,result):
            nonlocal events
            if event!="return" or frame.f_code not in (check_code,infer_code):
                return
            events += 1
            if events>200000 or events%256==0 and time.monotonic()-started>15:
                raise RuntimeError("diagnostic event/time guard")
            local = frame.f_locals
            if frame.f_code is check_code and result is False and len(failed)<4:
                failed.append((local["proof"],local["target"],local["ctx"]))
            parent = frame.f_back
            if (frame.f_code is infer_code and result is None and parent is not None
                    and parent.f_code is infer_code and len(strict)<4):
                strict.append((local["proof"],parent.f_locals.get("proof"),local["ctx"]))
        if sys.getprofile() is not None:
            raise RuntimeError("existing profiler")
        try:
            sys.setprofile(profile)
            accepted = checker.check((),proof,target)
        finally:
            sys.setprofile(None)
        wanted = {id(p) for p,_,_ in failed}
        wanted.update(id(p) for pair in strict for p in pair[:2])
        paths = _paths(proof,wanted)
        results.append(dict(name=name,local_body_accepted=accepted,structure=structure,events=events,
            first_failed_checks=[dict(path=paths.get(id(p)),proof_type=type(p).__name__,target=formula_record(f),
                inferred=formula_record(checker._infer(ctx,p,False)),context_length=len(ctx)) for p,f,ctx in failed],
            first_strict_failures=[dict(path=paths.get(id(p)),proof_type=type(p).__name__,parent_type=type(parent).__name__,
                parent_path=paths.get(id(parent)),context_length=len(ctx)) for p,parent,ctx in strict]))
        if not accepted:
            break
    if pins()!=before:
        raise RuntimeError("diagnostic inputs changed")
    return dict(schema="sqrt2-power-width-transport-v2-local-diagnostic-v1",source_pins=before,results=results,
        wall_seconds=time.monotonic()-started,kernel_mutations=0,producer_mutations=0,ancestor_proofs_checked=0,
        proof_artifacts_written=0,IR_parents_closed=0,library_admissions=0,
        authority="diagnostic_only_not_a_closed_power_width_proof")


if __name__=="__main__":
    result = diagnose()
    raw = cv.canonical(result)
    if len(raw)>64*1024:
        raise RuntimeError("diagnostic output cap")
    print(raw.decode())
