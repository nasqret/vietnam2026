#!/usr/bin/env python3
"""One fixed authored P3 cost diagnostic, in a fresh interpreter per engine."""
from pathlib import Path
import argparse
import hashlib
import json
import resource
import signal
import sys
import time

APP = Path(__file__).resolve().parent
FROZEN = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--engine", choices=("original", "sharing"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError("Use isolated Python with bytecode disabled.")
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("P3 diagnostic deadline")))
    signal.setitimer(signal.ITIMER_REAL, 90)
    native = FROZEN / "peano-lab/py" if args.engine == "original" else APP / "native-v7"
    sys.path[:0] = [str(native), str(APP)]
    from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
    from peano_lab.engine.state import start, proof_size
    from peano_lab.engine.trace import TraceLogger
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import parse_formula_with_names
    from peano_lab.kernel.proofs import Axiom, Proof
    from peano_lab.ui.prove import ProofSession, SurfaceCapabilities, checked_surface_final, run_surface
    from proof_cost import measure_proof
    from dataclasses import fields

    original_kernel = FROZEN / "peano-lab/py/peano_lab/kernel"
    if {p.name:p.read_bytes() for p in original_kernel.glob("*.py")} != {
            p.name:p.read_bytes() for p in (native / "peano_lab/kernel").glob("*.py")}:
        raise ValueError("The kernel must be byte-identical to the preserved original.")
    equality = "(a+b)+(c+d)=(a+c)+(b+d)"
    conjunction = "(" + equality + ")"
    for _ in range(7):
        conjunction = "(" + equality + " /\\ " + conjunction + ")"
    theorem = "forall a b c d. " + conjunction
    commands = ["intro a", "intro b", "intro c", "intro d", "have shared : " + equality, "ring"]
    for _ in range(7):
        commands += ["split", "exact shared"]
    commands += ["exact shared"]
    target, names = parse_formula_with_names(theorem)
    caps = SurfaceCapabilities(label="hydra-p3-sharing-diagnostic-v1",
        allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
    owner = ProofSession(state=start(target, names), original_target=target,
        original_names=names, target_source=theorem, classical=False,
        trace=TraceLogger(session_id="p3-sharing-diagnostic"))
    began = time.monotonic()
    for command in commands:
        owner = run_surface(owner, command, capabilities=caps)
    native_seconds = time.monotonic() - began
    began = time.monotonic()
    certificate = checked_surface_final(owner.state, target)
    if owner.state.goals or not check((), certificate, target):
        raise ValueError("The original kernel did not check the whole theorem.")
    checking_seconds = time.monotonic() - began
    began = time.monotonic()
    replay = run_proof(theorem, tuple(commands), capabilities=caps,
                       request_id="p3-independent-replay", classical=False)
    replay_seconds = time.monotonic() - began
    if replay.status != "proved" or not replay.kernel_checked or replay.goals \
            or replay.proof_nodes != proof_size(certificate):
        raise ValueError("Independent replay disagrees with the complete certificate.")
    axioms, seen, pending = set(), set(), [certificate]
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        if type(node) is Axiom:
            axioms.add(node.name)
        pending.extend(value for field in fields(node)
                       if isinstance((value := getattr(node, field.name)), Proof))
    record = {"schema":"hydra-p3-sharing-diagnostic-v1", "engine":args.engine,
        "theorem":theorem, "commands":commands, "kernel_checked":True,
        "independent_replay_checked":True, "classical":False,
        "axioms":sorted(axioms), "proof_cost":measure_proof(certificate, stage="final"),
        "native_seconds":native_seconds, "checking_seconds":checking_seconds,
        "independent_replay_seconds":replay_seconds,
        "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope":"Authored repeated-lemma diagnostic; one run per version, no search or benchmark claim."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"engine":args.engine,"proof_cost":record["proof_cost"],"axioms":record["axioms"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
