"""Inert test objects only: importing the native dataclasses runs no proofs."""
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
ROOT = next(parent for parent in APP.parents if
            (parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831").is_dir())
NATIVE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py"
sys.path[:0] = [str(APP), str(ROOT / "hydra-playground"), str(NATIVE)]

from peano_lab.engine.state import Goal, Hole, ProofState
from peano_lab.kernel.formulas import Eq, Exists, Forall
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.ui.prove import SurfaceCapabilities
from adviser_protocol import canonical_json, external_request


CAPS = SurfaceCapabilities(label="p8-pure-ast-tests", allowed_commands=frozenset(
    {"exists", "ring", "trans", "symm", "rewrite", "refl"}), allowed_theorems=frozenset())
AUTHORITY = "1" * 64


def state(target=None, *, variables=("a",), context=(), goals=None, original=None):
    if target is None:
        target = Eq(Var(0), Var(0))
    if goals is None:
        goals = (Goal(context, target, variables),)
    return ProofState(tuple(goals), Hole(0), (), target if original is None else original,
                      {}, variables)


def identity(backend):
    return {"backend": backend, "version": {"sympy": "1.14.0", "cvc5": "1.3.4", "vampire": "5.0.1"}[backend],
            "profile": "deep", "policy": "test-pinned-runtime", "package_sha256": "2" * 64,
            "helper_sha256": "3" * 64}


def request(backend="sympy", data=b"bounded exact stdin"):
    context = canonical_json({"schema": "hydra-adviser-semantic-context-v1", "test": True})
    return external_request(backend, data, context, identity(backend))


def execution(req, *, status="completed", executed=True, elapsed=0.25, exit_code=0):
    return {"status": status, "executed": executed, "elapsed_seconds": elapsed,
            "input_sha256": req.input_sha256, "exit_code": exit_code,
            "quiescent": True}


class Clock:
    def __init__(self, value=100.0):
        self.value = value

    def __call__(self):
        return self.value
