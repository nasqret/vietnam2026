#!/usr/bin/env python3
"""Build one fixed small library from project-owned, natively checked proofs.

The producer runs separately from the read-only request worker. Its scripts are
not included in the certificate data or sent to statement-only search.
"""
from pathlib import Path
import argparse
import hashlib
import json
import resource
import signal
import sys
import time

APP = Path(__file__).resolve().parent
BUILTINS = (
    "zero_add", "add_succ_left", "add_comm", "add_assoc", "mul_zero_left",
    "mul_succ_left", "mul_comm", "mul_add", "mul_assoc", "one_mul", "mul_one",
    "succ_ne_zero", "succ_injective", "add_right_cancel", "multiple_zero",
    "multiple_refl", "multiple_add",
)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError("Run in isolated Python without bytecode writes.")
    resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("Library build exceeded 300 seconds")))
    signal.setitimer(signal.ITIMER_REAL, 300)
    sys.path[:0] = [str(APP / "native-v7"), str(APP)]
    from certificate_codec import encode_certificate
    from lemma_library import KERNEL_IDENTITY_SHA256, load_library
    from peano_lab.library.theorems import replay
    from peano_lab.kernel.formulas import parse_formula_with_names
    from peano_lab.engine.state import start
    from peano_lab.engine.trace import TraceLogger
    from peano_lab.ui.prove import ProofSession, run_surface, checked_surface_final, SurfaceCapabilities
    from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
    from proof_cost import measure_proof

    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "certificates").mkdir()
    began = time.monotonic()
    entries, evidence = [], []

    def retain(name, statement, formula, certificate, dependencies, family, method):
        raw = encode_certificate(formula, certificate)
        relative = "certificates/" + name + ".json"
        (args.output / relative).write_bytes(raw)
        entries.append({"name":name,"statement":statement,
            "statement_sha256":hashlib.sha256(statement.encode()).hexdigest(),
            "family":family,"dependencies":list(dependencies),
            "certificate":{"path":relative,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}})
        evidence.append({"name":name,"method":method,"proof_cost":measure_proof(certificate,stage="final"),
                         "kernel_checked":True})
        print(json.dumps({"name":name,"bytes":len(raw),"proof_cost":evidence[-1]["proof_cost"]}),flush=True)

    for name in BUILTINS:
        checked = replay(name)
        family = ("natural_cancellation" if "cancel" in name else
                  "divisibility_witness_composition" if name == "multiple_add" else
                  "divisibility_foundations" if name.startswith("multiple_") else "arithmetic_foundations")
        retain(name,checked.spec.statement,checked.formula,checked.certificate,
               checked.spec.dependencies,family,"Replay of existing project-owned native theorem ladder")
    theorem = "forall n. exists k. n+n=2*k"
    commands = ("intro n", "exists n", "ring")
    formula, names = parse_formula_with_names(theorem)
    caps = SurfaceCapabilities(label="hydra-lemma-producer-v1", allowed_commands=MODEL_V1_COMMANDS,
                               allowed_theorems=frozenset())
    owner = ProofSession(state=start(formula,names), original_target=formula,
        original_names=names,target_source=theorem,classical=False,trace=TraceLogger(session_id="lemma-producer"))
    for command in commands:
        owner = run_surface(owner,command,capabilities=caps)
    certificate = checked_surface_final(owner.state,formula)
    independent = run_proof(theorem,commands,capabilities=caps,request_id="lemma-producer-replay")
    if independent.status != "proved" or not independent.kernel_checked or independent.goals:
        raise ValueError("Independent parity lemma replay failed.")
    retain("double_even",theorem,formula,certificate,(),"parity_foundations","Authored three-command proof and independent full-script replay")
    manifest = {"schema":"hydra-certified-lemma-library-v1","version":1,
        "capability_profile":"hydra-certified-lemmas-v1","kernel_identity_sha256":KERNEL_IDENTITY_SHA256,
        "entries":entries}
    raw = (json.dumps(manifest,indent=2)+"\n").encode()
    (args.output / "manifest.json").write_bytes(raw)
    identity = hashlib.sha256(raw).hexdigest()
    load_library(args.output,expected_manifest_sha256=identity,target=None)
    (args.output / "build-evidence.json").write_text(json.dumps({"schema":"hydra-lemma-build-evidence-v1",
        "manifest_sha256":identity,"entries":evidence,"elapsed_seconds":time.monotonic()-began,
        "all_certificates_reloaded_and_kernel_checked":True,"training_data":False,
        "producer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+"\n")
    print(json.dumps({"status":"complete","manifest_sha256":identity,"entries":len(entries)}),flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
