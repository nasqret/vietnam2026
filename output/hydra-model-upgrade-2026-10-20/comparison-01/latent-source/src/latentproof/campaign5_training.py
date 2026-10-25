"""Opt-in Campaign 5 training controls; imports no model or checker.

Execute validation/tests only in WMI/Helios SLURM. The historical trainer does
not call these helpers unless its recipe explicitly contains ``campaign5``.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import random

FORMAT = "latent-campaign5-training-v1"
ARMS = {"qwen_vanilla", "qwen_fixed", "qwen_random", "qwen_adaptive"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_options(cfg, arm):
    value = cfg.get("campaign5")
    if value is None:
        return None
    fields = {"format", "checkpoint_selection", "selection_policies",
              "proof_eval_steps", "adaptive_warmup_steps", "lr_multipliers",
              "training_budget_scope"}
    require(type(value) is dict and fields <= set(value) <= fields | {"sampling"} and value["format"] == FORMAT,
            "invalid exact Campaign 5 training control schema")
    require(value["checkpoint_selection"] in {"loss", "proof_success"},
            "checkpoint selection must be loss or proof_success")
    require(type(value["selection_policies"]) is dict
            and set(value["selection_policies"]) == set(cfg["arms"])
            and set(cfg["arms"]) <= ARMS and arm in cfg["arms"],
            "each registered arm needs one explicit checkpoint-selection policy")
    for name, policy in value["selection_policies"].items():
        require(type(policy) is dict and policy.get("kind") in {"fixed", "learned"},
                "selection policy must be fixed or learned")
        if policy["kind"] == "fixed":
            require(set(policy) == {"kind", "depth"} and type(policy["depth"]) is int
                    and 1 <= policy["depth"] <= cfg["max_recurrence"], "invalid fixed selection depth")
        else:
            require(name == "qwen_adaptive" and set(policy) == {"kind", "quantile"}
                    and type(policy["quantile"]) in {int, float}
                    and math.isfinite(policy["quantile"]) and 0 < policy["quantile"] <= 1,
                    "invalid learned selection policy")
        require(name != "qwen_vanilla" or policy == {"kind": "fixed", "depth": 1},
                "vanilla must select at its single-pass policy")
    steps = value["proof_eval_steps"]
    require(type(steps) is list and steps and all(type(step) is int and 1 <= step <= cfg["steps"] for step in steps)
            and steps == sorted(set(steps)) and steps[-1] == cfg["steps"],
            "proof milestones must be unique, increasing, and include the final update")
    require(type(value["adaptive_warmup_steps"]) is int
            and 0 <= value["adaptive_warmup_steps"] < cfg["steps"], "invalid all-depth warmup length")
    require(type(value["lr_multipliers"]) is dict
            and set(value["lr_multipliers"]) == {"lora", "damping", "gate"}
            and all(type(number) in {int, float} and math.isfinite(number) and number > 0
                    for number in value["lr_multipliers"].values()), "invalid parameter learning-rate multipliers")
    require(value["training_budget_scope"] in {"training", "elapsed"}, "invalid training budget scope")
    require(cfg.get("data_contract", {}).get("development_split") == "dev",
            "Campaign 5 checkpoint selection requires pinned train/dev/test data")
    require(cfg["evaluation_seconds_limit"] >= len(steps) * cfg["generation_seconds_per_event"],
            "cumulative proof-evaluation budget must reserve every registered milestone")
    require(cfg["proof_tasks"] > 0, "proof selection needs a nonempty development roster")
    sampling = value.get("sampling", {"kind": "permutation"})
    require(type(sampling) is dict and set(sampling) == {"kind"}
            and sampling["kind"] in {"permutation", "family_phase_balanced"}, "invalid explicit sampling strategy")
    return value


class BalancedExampleStream:
    """Exact resumable equal-family, equal setup/reasoning permutation streams.

    Each cycle visits every (task_family, phase) bucket once in shuffled order.
    Each bucket independently exhausts a shuffled row permutation before reuse.
    Phase is the literal leading tactic: ``intro`` is setup, every other tactic
    is reasoning. This is a transparent sampling heuristic, not a claim that
    every non-intro action is equally difficult or that setup is unimportant.
    """
    FORMAT = "latent-c5-family-phase-stream-v1"

    def __init__(self, rows, seed):
        require(rows and len({row["id"] for row in rows}) == len(rows), "empty or duplicate sampler rows")
        require(all(row["split"] == "train" for row in rows), "balanced sampler only accepts training rows")
        self.rows, self.rng = rows, random.Random(seed + 610341)
        self.buckets = {}
        for index, row in enumerate(rows):
            phase = "setup" if row["completion"].split()[0] == "intro" else "reasoning"
            key = row["task_family"] + "/" + phase
            self.buckets.setdefault(key, []).append(index)
        self.keys = sorted(self.buckets)
        families = {row["task_family"] for row in rows}
        require(set(self.keys) == {family + "/" + phase for family in families for phase in ("setup", "reasoning")},
                "every task family must have both setup and reasoning rows")
        self.identity = hashlib.sha256(json.dumps({key: [rows[i]["id"] for i in self.buckets[key]] for key in self.keys},
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.orders = {key: [] for key in self.keys}
        self.offsets = {key: 0 for key in self.keys}
        self.counts = {key: 0 for key in self.keys}
        self.cycle, self.cursor = [], 0

    def take(self, count):
        require(type(count) is int and count > 0, "positive integer sample size required")
        selected = []
        for _ in range(count):
            if self.cursor == len(self.cycle):
                self.cycle = self.keys[:]
                self.rng.shuffle(self.cycle)
                self.cursor = 0
            key = self.cycle[self.cursor]
            self.cursor += 1
            if self.offsets[key] == len(self.orders[key]):
                self.orders[key] = self.buckets[key][:]
                self.rng.shuffle(self.orders[key])
                self.offsets[key] = 0
            selected.append(self.rows[self.orders[key][self.offsets[key]]])
            self.offsets[key] += 1
            self.counts[key] += 1
        return selected

    def state_dict(self):
        return {"format": self.FORMAT, "identity": self.identity, "orders": {key: order[:] for key, order in self.orders.items()},
                "offsets": dict(self.offsets), "counts": dict(self.counts), "cycle": self.cycle[:],
                "cursor": self.cursor, "rng": self.rng.getstate()}

    def load_state_dict(self, state):
        require(type(state) is dict and set(state) == {"format", "identity", "orders", "offsets", "counts", "cycle", "cursor", "rng"}
                and state["format"] == self.FORMAT and state["identity"] == self.identity,
                "sampler format or ordered training corpus differs from checkpoint")
        require(all(set(state[field]) == set(self.keys) for field in ("orders", "offsets", "counts")), "sampler buckets changed")
        require(state["cycle"] == [] or sorted(state["cycle"]) == self.keys, "invalid sampler bucket cycle")
        require(type(state["cursor"]) is int and 0 <= state["cursor"] <= len(state["cycle"]), "invalid sampler cycle position")
        for key in self.keys:
            order, offset, count = state["orders"][key], state["offsets"][key], state["counts"][key]
            require(order == [] or sorted(order) == self.buckets[key], "invalid bucket row permutation")
            require(type(offset) is int and 0 <= offset <= len(order)
                    and type(count) is int and count >= 0, "invalid bucket accounting")
        self.orders = {key: order[:] for key, order in state["orders"].items()}
        self.offsets, self.counts = dict(state["offsets"]), dict(state["counts"])
        self.cycle, self.cursor = state["cycle"][:], state["cursor"]
        self.rng.setstate(state["rng"])

    def summary(self):
        return {"kind": "family_phase_balanced", "ordered_buckets_sha256": self.identity,
                "bucket_rows": {key: len(rows) for key, rows in self.buckets.items()}, "sampled_rows": dict(self.counts),
                "phase_definition": "literal intro command is setup; all other commands are reasoning"}


def stage_at(options, arm, step):
    if arm != "qwen_adaptive":
        return {"name": "fixed-depth-supervision", "mode": "fixed", "gate_enabled": False}
    if options is not None and step <= options["adaptive_warmup_steps"]:
        return {"name": "ungated-all-depth-warmup", "mode": "all_depth", "gate_enabled": False}
    return {"name": "adaptive-gate-training", "mode": "adaptive", "gate_enabled": True}


def parameter_group(name):
    if name.startswith("halt_gate."):
        return "gate"
    if name == "damping_logits":
        return "damping"
    return "lora"


def graceful_stop(options, *, stop_requested, at_budget_limit, step, total_steps):
    """Save before new validation work when an opt-in run must relinquish compute."""
    return options is not None and (stop_requested or (at_budget_limit and step < total_steps))


def optimizer_groups(model, options, learning_rate):
    """Partition existing trainable tensors; never change requires_grad flags."""
    groups = {name: [] for name in ("lora", "damping", "gate")}
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            groups[parameter_group(name)].append(parameter)
    return [{"params": parameters, "name": name,
             "lr_multiplier": options["lr_multipliers"][name],
             "lr": learning_rate * options["lr_multipliers"][name]}
            for name, parameters in groups.items() if parameters]


def proof_candidate(report, proofs_path, *, policy, validation_loss, step, frozen_tasks, success_label=None):
    """Construct a rank only from complete, greedy, dev-only proof receipts.

    Ranking: more proofs, fewer ACTUAL forward block calls over the whole proof
    roster, lower loss at the same explicit policy, then earlier checkpoint.
    Failed attempts remain in both the denominator and the cost accounting.
    No success is inferred from teacher-forced targets or intermediate validity.
    """
    require(report.get("split") == "dev" and report.get("test_parsed") is False
            and report.get("selection_usage") == "development-model-selection"
            and report.get("validation_used_for_selection") is True,
            "proof checkpoint selection must use development-only evaluation")
    require(report.get("provenance", {}).get("policy") == policy,
            "proof checkpoint policy differs from registered selection policy")
    require(report["provenance"].get("checkpoint_step") == step
            and report["provenance"].get("checkpoint_role") == "current-evaluation-snapshot",
            "proof evaluation is not bound to this current checkpoint step")
    counts, roster = report["proof_counts"], report["proof_task_ids"]
    require(roster and len(roster) == len(set(roster)), "empty or duplicate proof roster")
    require(type(frozen_tasks) is list and [task["id"] for task in frozen_tasks] == roster
            and all(task["split"] == "dev" for task in frozen_tasks), "proof roster differs from the frozen development task objects")
    require(type(validation_loss) in {int, float} and math.isfinite(validation_loss)
            and type(step) is int and step > 0, "invalid checkpoint rank inputs")
    require(success_label is None or callable(success_label), "invalid native success-label callback")
    success_label = (lambda action: action) if success_label is None else success_label
    path = Path(proofs_path)
    require(hashlib.sha256(path.read_bytes()).hexdigest() == report["proofs_sha256"],
            "proof receipts differ from completed summary")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    require([row["id"] for row in rows] == roster, "proof cost receipts differ from the ordered dev roster")
    complete = (report["status"] == "completed" and counts.get("selected") == len(roster)
                and counts.get("attempted") == len(roster) and counts.get("recorded") == len(roster)
                and counts.get("wall_budget_limited", 0) == 0)
    if not complete:
        return None
    total, solved = {name: 0 for name in ("block_calls", "head_calls", "gate_calls", "decision_tokens")}, 0
    for row, task in zip(rows, frozen_tasks):
        task_hash = hashlib.sha256(json.dumps(task, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
        require(row.get("task_sha256") == task_hash and row.get("session_id") == task["session_id"]
                and row.get("formula") == task["formula"]
                and row.get("environment_sha256") == task["environment_sha256"],
                "proof receipt lost its exact frozen development task/authority binding")
        require(row.get("model_calls", 0) > 0 and row.get("reference_actions_used") == 0
                and row.get("search_branches") == 1 and row.get("restarts") == 0
                and not row.get("wall_budget_limited", True), "selection receipts are not complete intrinsic greedy rollouts")
        require(type(row.get("steps")) is list and len(row["steps"]) == row["model_calls"],
                "proof selection model call and generation receipt counts differ")
        require(type(row["autonomous_python_kernel_proof"]) is bool, "invalid native proof verdict")
        success = row["autonomous_python_kernel_proof"]
        require((row.get("status") == "proved") is success, "rollout status contradicts its native proof verdict")
        native = row.get("native_result")
        if success:
            require(type(native) is dict and native.get("status") == "proved"
                    and native.get("kernel_checked") is True and native.get("classical") is False
                    and native.get("theorem") == row["formula"]
                    and native.get("environment_sha256") == row["environment_sha256"]
                    and native.get("goals") == [] and row.get("remaining_goals") == []
                    and type(native.get("trace")) is list and native["trace"]
                    and native["trace"][-1].get("qed") is True,
                    "selected success lacks explicit original-target constructive kernel QED")
            actions = row["actions"]
            transitions = [entry for entry in native["trace"] if "v" in entry]
            require(actions and len(actions) == row["accepted_actions"] == row["submitted_actions"]
                    == native.get("tactics_requested") == native.get("tactics_applied") == len(transitions)
                    and native.get("failed_tactics") == 0
                    and all(entry.get("status") == "ok" for entry in transitions),
                    "selected success has incomplete native accepted-action accounting")
            require(len(row["steps"]) == len(actions), "selected success has unbound generated steps")
            previous = task["initial_state"]
            for number, (action, generated, transition) in enumerate(zip(actions, row["steps"], transitions), 1):
                require(generated.get("index") == number and generated.get("valid_transition") is True
                        and generated.get("decoded", {}).get("valid_action") is True
                        and generated["decoded"].get("action") == action
                        and transition.get("step") == number and transition.get("goals_before") == previous
                        and transition.get("tactic") == success_label(action),
                        "selected success native trajectory differs from its actual generated actions")
                previous = transition["goals_after"]
            require(previous == [], "selected success native action trajectory leaves open goals")
        else:
            require(native is None or native.get("kernel_checked") is not True,
                    "complete rollout hides a successful native kernel result")
        solved += int(row["autonomous_python_kernel_proof"])
        for action in row["steps"]:
            generation = action["generation"]
            require(generation.get("provenance") == report["provenance"],
                    "proof selection generation provenance drift")
            length = len(generation["decision_ids"])
            total["decision_tokens"] += length
            for field in ("block_calls", "head_calls", "gate_calls"):
                values = generation[field]
                require(type(values) is list and len(values) == length
                        and all(type(number) is int and number >= 0 for number in values),
                        "missing actual per-decision forward-cost telemetry")
                total[field] += sum(values)
    require(solved == counts.get("autonomous_python_kernel_proof", 0), "summary proof total differs from receipts")
    contract = report["evaluation_contract"]
    # Actual available seconds can differ by initialization milliseconds. The
    # registered ceiling, corpus, roster, and action/token limits must be exact.
    stable_keys = ("dataset_id", "split", "preparation_sha256", "admission_sha256",
        "selection_object_sha256", "ordered_roster_sha256", "authority_inventory_sha256",
        "task_metadata_sha256", "budgets", "budget_ceiling", "wall_seconds_ceiling")
    return {"criterion": "dev-proof-success-actual-blocks-loss-earliest-v1",
            "selection_policy": policy, "step": step, "solved": solved,
            "selected": len(roster), "complete": True, "cost": total,
            "validation_loss": validation_loss,
            "rank": [-solved, total["block_calls"], validation_loss, step],
            "proofs_sha256": report["proofs_sha256"],
            "evaluated_checkpoint_sha256": report["provenance"]["checkpoint_sha256"],
            "evaluated_checkpoint_step": step,
            "evaluation_contract": contract,
            "comparison_contract": {key: contract[key] for key in stable_keys},
            "test_used": False,
            "cost_scope": "logical forward calls on all proof attempts, excluding backward and teacher-forced probes"}


def candidate_is_better(candidate, incumbent):
    if candidate is None:
        return False
    if incumbent is None:
        return True
    require(candidate["comparison_contract"] == incumbent["comparison_contract"]
            and candidate["selection_policy"] == incumbent["selection_policy"],
            "checkpoint comparison changed the frozen development protocol")
    return tuple(candidate["rank"]) < tuple(incumbent["rank"])
