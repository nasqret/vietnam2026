#!/usr/bin/env python3
"""Bounded, non-authoritative profiling of the unchanged CV048-v1 local bodies.

No ancestor is assumed as an admitted theorem and no proof artifact is written.
Only the dependency-curried authoring bodies are observed under the original
checker. The external supervisor must enforce 15 CPU / 20 wall seconds,
768 MiB RSS and 64 KiB output. This is diagnosis, not a certificate retry.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

import sqrt2_power_convolution_total as cv
from diagnose_sqrt2_power_convolution import _proof_children,_structure,_paths
from sqrt2_power_definitions import parse_named
from peano_lab.kernel import checker
from peano_lab.kernel.formulas import Imp,pretty_formula
from peano_lab.library.proof_bundle import encode_formula

PINS = {
    "scripts/sqrt2_power_convolution_total.py":"01a758ef16a32da0e6ae4790b085168668396b07707eb11086127aee6b527414",
    "peano-lab/py/peano_lab/kernel/checker.py":"d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "scripts/diagnose_sqrt2_power_convolution.py":"2592bf12f09eef6e79d7495c71aa375089da6e09c2f931cfe2842e04ac7a8c9b",
}


def pins():
    result = cv.convolution_total_source_pins()
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
    return dict(bytes=len(raw),sha256=sha256(raw).hexdigest(),pretty=pretty_formula(formula,[f"v{i}" for i in range(64)])[:2500])


def diagnose():
    started,before = time.monotonic(),pins()
    registry = cv.definition_registry()
    sources = {**cv.ENDPOINT_SOURCES,**cv.HELPER_SOURCES,"CV048":cv.NAMED_SOURCE}
    formulas = {name:parse_named(source,registry=registry) for name,source in sources.items()}
    factories = {"rows_prefix":lambda s:cv._rows_prefix(s,registry),"column_entry":lambda s:cv._column_entry(s,registry),
        "column_linear":cv._column_linear,"column_tail":lambda s:cv._column_tail(s,registry),"CV048":lambda s:cv._root(s,registry)}
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
    return dict(schema="sqrt2-power-convolution-total-v1-local-diagnostic-v1",source_pins=before,results=results,
        wall_seconds=time.monotonic()-started,kernel_mutations=0,producer_mutations=0,ancestor_proofs_checked=0,
        proof_artifacts_written=0,IR_parents_closed=0,library_admissions=0,
        authority="diagnostic_only_not_a_closed_convolution_proof")


if __name__=="__main__":
    result = diagnose()
    raw = cv.canonical(result)
    if len(raw)>64*1024:
        raise RuntimeError("diagnostic output cap")
    print(raw.decode())
