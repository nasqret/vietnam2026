"""Small, optional branch-cost model. Importing this module does no training.

The target is observed distance along a completed, kernel-checked continuation,
not theorem truth or the probability that an uncompleted branch is impossible.
Every goal contributes features. Resource-censored observations are never fitted.
The caller retains scheduling, fairness, proof authority, and all native budgets.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import time

SCHEMA = "hydra-linear-branch-ranker-v1"
FEATURE_SCHEMA = "hydra-all-goal-features-v1"
MAX_GOALS = 64
MAX_STATE_BYTES = 65536
MAX_ROWS = 4096
MAX_FIT_SECONDS = 20.0
FEATURES = (
    "goal_count", "state_bytes", "largest_goal_bytes", "target_bytes",
    "context_bytes", "universal_count", "existential_count", "implication_count",
    "conjunction_count", "disjunction_count", "equality_count", "product_count",
    "sum_count", "successor_count", "metavariable_count", "max_parenthesis_depth",
    "branch_depth", "objects", "occurrences", "certificate_depth",
    "cost_missing", "objects_inexact", "occurrences_inexact", "depth_inexact",
    "remaining_depth", "remaining_tactics", "remaining_missing",
)
_COST_MAX = {"distinct_objects": 100000, "structural_occurrences": 500000, "depth": 256}


class RankerError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise RankerError(message)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def validate_goals(goals, *, allow_empty=True):
    _require(type(goals) in (list, tuple) and len(goals) <= MAX_GOALS,
             "A complete, bounded sequence of goals is required.")
    _require(allow_empty or bool(goals), "An open state must contain a goal.")
    _require(all(type(goal) is str and goal and goal.count("⊢") == 1
                 and "\n" not in goal and "\r" not in goal for goal in goals),
             "Each goal must be exact one-line native context/target text.")
    _require(sum(len(goal.encode("utf-8")) for goal in goals) <= MAX_STATE_BYTES,
             "Full state exceeds its byte bound; truncation is forbidden.")
    return tuple(goals)


def extract_features(all_goals, *, depth=0, proof_cost=None, remaining_budget=None):
    """Return fixed bounded features, including explicit missing-cost indicators.

    Formula symbols are counted in native-rendered text; these are structural
    proxies, not a second parser or a mathematical simplifier. Cost must be a
    measurement of THIS partial state, never a future final-proof measurement.
    Unknown cost/budget is distinguishable from observed zero.
    """
    goals = validate_goals(all_goals)
    _require(type(depth) is int and 0 <= depth <= 512, "Invalid branch depth.")
    sizes = [len(goal.encode("utf-8")) for goal in goals]
    targets = [goal.split("⊢", 1)[1].strip() for goal in goals]
    contexts = [goal.split("⊢", 1)[0] for goal in goals]
    text = "\n".join(goals)
    nesting = maximum = 0
    for character in text:
        if character == "(":
            nesting += 1
            maximum = max(maximum, nesting)
        elif character == ")":
            nesting = max(0, nesting - 1)
    def scaled(number, bound):
        return math.log1p(min(max(number, 0), bound)) / math.log1p(bound)
    result = {
        "goal_count": len(goals) / MAX_GOALS,
        "state_bytes": scaled(sum(sizes), MAX_STATE_BYTES),
        "largest_goal_bytes": scaled(max(sizes, default=0), MAX_STATE_BYTES),
        "target_bytes": scaled(sum(len(x.encode("utf-8")) for x in targets), MAX_STATE_BYTES),
        "context_bytes": scaled(sum(len(x.encode("utf-8")) for x in contexts), MAX_STATE_BYTES),
        "universal_count": scaled(text.count("∀"), 4096),
        "existential_count": scaled(text.count("∃"), 4096),
        "implication_count": scaled(text.count("→"), 4096),
        "conjunction_count": scaled(text.count("∧"), 4096),
        "disjunction_count": scaled(text.count("∨"), 4096),
        "equality_count": scaled(text.count("="), 8192),
        "product_count": scaled(text.count("·") + text.count("*"), 8192),
        "sum_count": scaled(text.count("+"), 8192),
        "successor_count": scaled(len(re.findall(r"\bS\b", text)), 8192),
        "metavariable_count": scaled(text.count("?"), 4096),
        "max_parenthesis_depth": scaled(maximum, 256),
        "branch_depth": depth / 512,
    }
    _require(proof_cost is None or type(proof_cost) is dict, "Invalid cost observation.")
    cost = proof_cost or {}
    exact = cost.get("exact", {})
    _require(type(exact) is dict, "Invalid cost exactness map.")
    missing = False
    for field, feature, flag in (("distinct_objects", "objects", "objects_inexact"),
                                 ("structural_occurrences", "occurrences", "occurrences_inexact"),
                                 ("depth", "certificate_depth", "depth_inexact")):
        value = cost.get(field)
        if value is None:
            missing = True
            result[feature], result[flag] = 0.0, 1.0
        else:
            _require(type(value) is int and value >= 0, "Invalid measured certificate cost.")
            _require(type(exact.get(field)) is bool, "Cost exactness must be explicit.")
            result[feature] = scaled(value, _COST_MAX[field])
            result[flag] = float(not exact[field])
    result["cost_missing"] = float(missing)
    _require(remaining_budget is None or type(remaining_budget) is dict,
             "Invalid remaining-budget observation.")
    budget = remaining_budget or {}
    missing_budget = False
    for key, bound in (("remaining_depth", 512), ("remaining_tactics", 50000)):
        value = budget.get(key)
        if value is None:
            missing_budget = True
            result[key] = 0.0
        else:
            _require(type(value) is int and value >= 0, "Invalid remaining budget.")
            result[key] = scaled(value, bound)
    result["remaining_missing"] = float(missing_budget)
    return {name: result[name] for name in FEATURES}


def validate_features(features):
    _require(type(features) is dict and set(features) == set(FEATURES),
             "Feature keys differ from the versioned ranker contract.")
    _require(all(_finite(value) and 0 <= value <= 1 for value in features.values()),
             "Features must be finite numbers in [0,1].")
    return tuple(float(features[name]) for name in FEATURES)


@dataclass(frozen=True)
class BranchRanker:
    weights: tuple[float, ...]
    intercept: float
    artifact_sha256: str

    def __post_init__(self):
        _require(type(self.weights) is tuple and len(self.weights) == len(FEATURES)
                 and all(_finite(x) and abs(x) <= 100 for x in self.weights)
                 and _finite(self.intercept) and abs(self.intercept) <= 100,
                 "Ranker parameters are not finite bounded coefficients.")
        _require(type(self.artifact_sha256) is str
                 and re.fullmatch(r"[0-9a-f]{64}", self.artifact_sha256) is not None,
                 "Ranker must identify its exact parameter artifact.")

    def score_features(self, features):
        vector = validate_features(features)
        # A scalar priority, not a calibrated likelihood or a native judgment.
        return max(0.0, min(20.0, self.intercept + sum(w*x for w,x in zip(self.weights, vector))))

    def score(self, all_goals, *, depth=0, proof_cost=None, remaining_budget=None):
        return self.score_features(extract_features(all_goals, depth=depth,
            proof_cost=proof_cost, remaining_budget=remaining_budget))

    def callback(self, *, all_goals, depth, proof_cost=None, remaining_budget=None):
        """Root can insert this finite scalar after mandatory scheduling tiers."""
        return self.score(all_goals, depth=depth, proof_cost=proof_cost,
                          remaining_budget=remaining_budget)


def _training_rows(rows):
    _require(type(rows) in (list, tuple) and 1 <= len(rows) <= MAX_ROWS,
             "Ranker fitting requires 1..4096 explicitly selected rows.")
    validated = []
    seen = set()
    for row in rows:
        _require(type(row) is dict and row.get("schema") == "hydra-branch-distance-v1"
                 and row.get("split") == "train" and row.get("censored") is False
                 and row.get("verified_continuation") is True,
                 "Only training-split checked continuation distances may be fitted.")
        identifier, distance = row.get("id"), row.get("remaining_steps")
        _require(type(identifier) is str and identifier not in seen,
                 "Duplicate/missing ranker row identity.")
        seen.add(identifier)
        _require(type(distance) is int and 0 <= distance <= 512, "Invalid observed distance.")
        validated.append((identifier, validate_features(row.get("features")), math.log1p(distance)))
    return sorted(validated)


def train_ranker(rows, *, seed=20260904, learning_rate=0.05, l2=0.01,
                 max_seconds=MAX_FIT_SECONDS, should_stop=None):
    """Fit one deterministic pass of bounded squared-loss linear regression.

    Deliberately explicit, never run on import/export. A soft deadline raises
    instead of publishing a partially trained artifact. No restart or resume.
    """
    _require(type(seed) is int and 0 <= seed <= 2**32-1, "Invalid seed.")
    _require(_finite(learning_rate) and 0 < learning_rate <= 0.1
             and _finite(l2) and 0 <= l2 <= 1 and _finite(max_seconds)
             and 0 < max_seconds <= MAX_FIT_SECONDS, "Invalid bounded fit settings.")
    data = _training_rows(rows)
    # Seed affects ordering without depending on Python's randomized hash seed.
    data.sort(key=lambda item: hashlib.sha256(f"{seed}:{item[0]}".encode()).hexdigest())
    started = time.monotonic()
    weights, intercept = [0.0] * len(FEATURES), 0.0
    for _, vector, target in data:
        if time.monotonic()-started >= max_seconds or (should_stop is not None and should_stop()):
            raise RankerError("Ranker fit stopped; no completed artifact was produced.")
        error = max(-10.0, min(10.0, intercept + sum(w*x for w,x in zip(weights,vector)) - target))
        intercept -= learning_rate * error
        weights = [max(-100.0, min(100.0, w-learning_rate*(error*x+l2*w)))
                   for w,x in zip(weights,vector)]
    def loss():
        return sum((intercept+sum(w*x for w,x in zip(weights,v))-y)**2 for _,v,y in data)/len(data)
    return {"schema": SCHEMA, "feature_schema": FEATURE_SCHEMA, "features": list(FEATURES),
        "weights": weights, "intercept": intercept, "trained": True,
        "target": "log1p_observed_checked_continuation_steps", "lower_is_better": True,
        "fit": {"algorithm": "one_pass_clipped_sgd_squared_loss", "epochs": 1,
                "rows": len(data), "seed": seed, "learning_rate": learning_rate,
                "l2": l2, "training_mse": loss(), "elapsed_seconds": time.monotonic()-started,
                "training_row_ids_sha256": hashlib.sha256(canonical(sorted(x[0] for x in data))).hexdigest()},
        "resource_censored_rows_used": 0, "theorem_truth_prediction": False,
        "mathematical_authority": False, "automatic_retry": False, "resumed": False,
        "usefulness_evaluated": False}


def load_ranker(path, *, expected_sha256):
    path = Path(path)
    _require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 65536,
             "Expected a small regular ranker JSON artifact.")
    raw = path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == expected_sha256, "Ranker artifact hash mismatch.")
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "Duplicate ranker JSON key.")
            result[key] = value
        return result
    record = json.loads(raw, object_pairs_hook=pairs,
                        parse_constant=lambda _: (_ for _ in ()).throw(RankerError("Nonfinite ranker JSON.")))
    _require(type(record) is dict and record.get("schema") == SCHEMA
             and record.get("feature_schema") == FEATURE_SCHEMA
             and record.get("features") == list(FEATURES) and record.get("trained") is True
             and record.get("target") == "log1p_observed_checked_continuation_steps"
             and record.get("lower_is_better") is True,
             "Ranker artifact has an unsupported schema or is not trained.")
    return BranchRanker(tuple(record.get("weights", [])), record.get("intercept"), expected_sha256)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--data-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    _require(not args.output.exists(), "Refusing to overwrite a ranker artifact.")
    _require(args.data.is_file() and not args.data.is_symlink()
             and args.data.stat().st_size <= 64*1024*1024, "Invalid bounded ranker input.")
    raw = args.data.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == args.data_sha256, "Ranker data hash mismatch.")
    rows = [json.loads(line) for line in raw.splitlines()]
    record = train_ranker(rows)
    record["data"] = {"path": str(args.data), "sha256": args.data_sha256, "bytes": len(raw)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as output:
        output.write(canonical(record)+b"\n")
    print(json.dumps({"trained": True, "rows": record["fit"]["rows"], "output": str(args.output),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
