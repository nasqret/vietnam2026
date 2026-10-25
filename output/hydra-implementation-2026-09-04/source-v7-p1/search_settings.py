"""Explicit, finite search presets for the local Hydra playground.

Profiles are application policy, not client-supplied arbitrary resource limits.
The original model-only algorithm remains restricted to its standard settings.
"""
from __future__ import annotations

from copy import deepcopy

POLICY = "hydra-search-settings-v1"
PROFILES = {
    "standard": {
        "name": "Standard", "description": "Quick exploration with the original resource budgets.",
        "model_calls": [8, 16], "default_model_calls": 16,
        "beams": [1, 4], "default_beam": 4,
        "frontiers": {1: 16, 4: 64},
        "worker": {"wall_seconds": 180, "cpu_seconds": 300, "rss_bytes": 8 * 1024**3,
                   "stdout_bytes": 2 * 1024**2},
        "search": {"max_depth": 32, "max_states": 256, "max_tactic_attempts": 1024,
                   "max_expansions": 128, "candidates_per_state": 24,
                   "max_macro_steps": 4, "closure_steps": 8, "heuristic_burst": 4,
                   "max_vampire_calls": 4, "wall_seconds": 150.0},
    },
    "deep": {
        "name": "Deep", "description": "More induction branches, witness candidates, and solver time.",
        "model_calls": [16, 32, 64], "default_model_calls": 32,
        "beams": [4, 8], "default_beam": 4,
        "frontiers": {4: 128, 8: 192},
        "worker": {"wall_seconds": 330, "cpu_seconds": 600, "rss_bytes": 8 * 1024**3,
                   "stdout_bytes": 8 * 1024**2},
        "search": {"max_depth": 96, "max_states": 2048, "max_tactic_attempts": 12000,
                   "max_expansions": 768, "candidates_per_state": 48,
                   "max_macro_steps": 8, "closure_steps": 16, "heuristic_burst": 8,
                   "max_vampire_calls": 12, "wall_seconds": 300.0},
    },
    "research": {
        "name": "Research", "description": "A larger local experiment; cancel at any time.",
        "model_calls": [32, 64, 128], "default_model_calls": 64,
        "beams": [4, 8], "default_beam": 8,
        "frontiers": {4: 192, 8: 256},
        "worker": {"wall_seconds": 660, "cpu_seconds": 1200, "rss_bytes": 8 * 1024**3,
                   "stdout_bytes": 16 * 1024**2},
        "search": {"max_depth": 160, "max_states": 8192, "max_tactic_attempts": 40000,
                   "max_expansions": 4096, "candidates_per_state": 64,
                   "max_macro_steps": 8, "closure_steps": 32, "heuristic_burst": 8,
                   "max_vampire_calls": 24, "wall_seconds": 600.0},
    },
}


def profile(name="standard"):
    if type(name) is not str or name not in PROFILES:
        raise ValueError("Search profile must be standard, deep, or research.")
    return {"id": name, "policy": POLICY, **deepcopy(PROFILES[name])}


def validate_selection(mode, name, model_calls, beam):
    selected = profile(name)
    if mode == "model" and name != "standard":
        raise ValueError("The original model-only search supports only the standard profile.")
    if type(model_calls) is not int or model_calls not in selected["model_calls"]:
        raise ValueError("Model-call budget for " + name + " must be one of "
                         + ", ".join(map(str, selected["model_calls"])) + ".")
    if type(beam) is not int or beam not in selected["beams"]:
        raise ValueError("Beam width for " + name + " must be one of "
                         + ", ".join(map(str, selected["beams"])) + ".")
    return selected


def native_limits(request):
    mode = request["search_mode"]
    selected = validate_selection(mode, request.get("search_profile", "standard"),
                                  request["max_model_calls"], request["beam_width"])
    limits = dict(selected["search"])
    limits.update(max_model_calls=request["max_model_calls"] if mode == "hybrid" else 0,
                  max_vampire_calls=limits["max_vampire_calls"] if mode in {"symbolic", "hybrid"} else 0,
                  max_frontier=selected["frontiers"][request["beam_width"]])
    return limits


def public_profiles():
    """Fresh JSON-safe metadata, including the exact public budget meanings."""
    from vampire_limits import solver_limits
    return {name: {**profile(name), "vampire": solver_limits(name)} for name in PROFILES}
