"""Untrusted hybrid candidate policies for Peano Lab's checked search."""

from pathlib import Path
import sys


_PEANO_PYTHON = Path(__file__).resolve().parents[2] / "peano-lab" / "py"
if _PEANO_PYTHON.is_dir() and str(_PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(_PEANO_PYTHON))

__all__ = [
    "HYDRA_POLICY_VERSION",
    "MACRO_ACTION_HEADS",
    "FixedCandidatePolicy",
    "HeadGate",
    "HeadRole",
    "HydraCandidatePolicy",
    "HydraPortfolioPolicy",
    "IdentifiedCandidatePolicy",
    "MacroAction",
    "NullCandidatePolicy",
    "PolicyHead",
    "ProposalOutcome",
    "ProposalRecord",
    "RecordedCandidatePolicy",
    "RecordedState",
    "ScriptCandidatePolicy",
]


def __getattr__(name: str) -> object:
    """Keep resource-control parents free of the native theorem catalog.

    Public policy exports retain their original objects. Importing a small
    utility such as ``review_runtime`` must not also allocate the proof
    library before its memory-bounded child has even started.
    """
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from . import policy

    value = getattr(policy, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
