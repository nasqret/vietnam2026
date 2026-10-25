"""Strict Qwen action checks and autonomous Peano validation rollouts.

Candidate destination: latentproof.qwen_eval. Execute only in authorized SLURM.
No model import occurs here. The callback owns model inference and must return
the full emitted BPE decisions, including an actually emitted terminal EOS.
Reference-prefix completion and autonomous original-target completion are
different metrics. Python kernel acceptance is NOT native Lean acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import sys
import time
import unicodedata

if __package__:
    from .qwen_data import (ADMISSION_SHA256, FORMAT as DATA_FORMAT, IntegrityError, ROW_FIELDS,
                           SELECTION_FORMAT, canonical, compact_prompt, decode, digest, group_sessions,
                           load_pinned_tokenizer, load_tokenized, object_digest, require, require_slurm,
                           tokenizer_identity, write_json)
else:
    from compact_qwen_data import (ADMISSION_SHA256, FORMAT as DATA_FORMAT, IntegrityError, ROW_FIELDS,
                                  SELECTION_FORMAT, canonical, compact_prompt, decode, digest, group_sessions,
                                  load_pinned_tokenizer, load_tokenized, object_digest, require, require_slurm,
                                  tokenizer_identity, write_json)

FORMAT = "latent-qwen-constructive-validation-v1"
GENERATION_FORMAT = "latent-qwen-bpe-generation-v1"
NATIVE_STATUSES = {"proved", "open", "tactic_error", "tactic_limit", "kernel_rejection"}
REJECTED_CATEGORIES = {"Cc", "Cf", "Cs", "Zl", "Zp"}
DEFAULT_BUDGETS = {"max_actions": 16, "max_new_tokens": 256, "max_total_decision_tokens": 4096,
                   "max_context_tokens": 1024, "candidates_per_step": 1, "search_width": 1}


def byte_decoder():
    values = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
    characters, extra = values[:], 0
    for value in range(256):
        if value not in values:
            values.append(value)
            characters.append(256 + extra)
            extra += 1
    return {chr(character): value for value, character in zip(values, characters)}


def validate_provenance(provenance):
    require(type(provenance) is dict, "missing generation provenance")
    for key in ("checkpoint_sha256", "tokenizer_identity_sha256", "source_inventory_sha256"):
        value = provenance.get(key)
        require(type(value) is str and len(value) == 64 and all(char in "0123456789abcdef" for char in value), f"invalid {key}")
    require(type(provenance.get("run_id")) is str and provenance["run_id"]
            and type(provenance.get("policy")) is dict and provenance["policy"], "missing run/policy provenance")
    require(type(provenance.get("model_vocab_size")) is int and provenance["model_vocab_size"] > 0, "missing model output vocabulary size")


def strict_generation(record, tokenizer, max_new_tokens, *, expected_provenance=None):
    """Check receipts, then return unmodified decoded action or model failures.

    Bad receipt structure/contradictory fields raise IntegrityError. Missing EOS,
    empty output, added/control tokens, tokenizer vocabulary holes, invalid UTF8,
    whitespace/envelopes and multiline output are model failures. A vocabulary
    hole can be a genuine argmax when lm_head is wider than the tokenizer.
    """
    require(type(record) is dict and type(max_new_tokens) is int and max_new_tokens > 0, "invalid generation request/record")
    ids = record.get("decision_ids")
    require(type(ids) is list and all(type(token) is int and token >= 0 for token in ids), "decisions must be nonnegative integer IDs, not booleans")
    require(len(ids) <= max_new_tokens, "generation exceeded supplied token budget")
    if expected_provenance is not None:
        validate_provenance(expected_provenance)
        require(record.get("format") == GENERATION_FORMAT, "wrong generation receipt format")
        require(canonical(record.get("provenance")) == canonical(expected_provenance), "generation model/tokenizer/source/policy identity drift")
    declared_size = record.get("model_vocab_size", (expected_provenance or {}).get("model_vocab_size", len(tokenizer)))
    require(type(declared_size) is int and declared_size >= len(tokenizer), "invalid declared model vocabulary")
    if expected_provenance is not None:
        require(declared_size == expected_provenance["model_vocab_size"], "model vocabulary differs from frozen provenance")
    require(all(token < declared_size for token in ids), "decision exceeds declared model output vocabulary")
    eos_id = tokenizer.eos_token_id
    require(type(eos_id) is int, "tokenizer lacks a concrete EOS ID")
    eos = bool(ids and ids[-1] == eos_id)
    require(type(record.get("eos")) is bool and record["eos"] is eos, "EOS flag disagrees with full emitted decisions")
    require(eos_id not in (ids[:-1] if eos else ids), "emitted decisions continue after EOS")
    reason = record.get("stop_reason")
    require(reason == "eos" if eos else reason in {"token_budget", "context_limit", "invalid_special_token", "wall_time_budget"}, "stop reason disagrees with actual EOS")
    if not eos and reason == "token_budget":
        require(len(ids) == max_new_tokens, "token-budget stop did not exhaust its supplied effective budget")
    if expected_provenance is not None:
        require(type(record.get("prompt_tokens")) is int and record["prompt_tokens"] > 0
                and type(record.get("max_context_tokens")) is int and record["max_context_tokens"] > record["prompt_tokens"]
                and record.get("max_new_tokens") == max_new_tokens, "missing or inconsistent generation input/budget receipt")
        require(record["prompt_tokens"] + len(ids) <= record["max_context_tokens"], "generation exceeded declared context")
        prompt_sha = record.get("prompt_sha256")
        require(type(prompt_sha) is str and len(prompt_sha) == 64 and all(char in "0123456789abcdef" for char in prompt_sha), "missing prompt byte binding")
    if not eos and reason == "context_limit":
        require(type(record.get("prompt_tokens")) is int and type(record.get("max_context_tokens")) is int
                and len(ids) == record["max_context_tokens"] - record["prompt_tokens"], "context-limit stop did not exhaust a bound actual context")
    payload = ids[:-1] if eos else ids
    reasons, raw, action = [], None, None
    added = set(tokenizer.get_added_vocab().values()) | set(getattr(tokenizer, "all_special_ids", []))
    if any(token >= len(tokenizer) for token in payload):
        reasons.append("unmapped_model_vocabulary_token")
    elif any(token in added for token in payload):
        reasons.append("foreign_added_or_special_token")
    else:
        tokens = tokenizer.convert_ids_to_tokens(payload)
        if not (type(tokens) is list and len(tokens) == len(payload) and all(type(token) is str for token in tokens)):
            reasons.append("unmapped_model_vocabulary_token")
        else:
            inverse = byte_decoder()
            try:
                raw = bytes(inverse[char] for token in tokens for char in token)
            except KeyError as exc:
                raise IntegrityError("tokenizer decoder is not the pinned ByteLevel mapping") from exc
            try:
                action = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                reasons.append("invalid_utf8")
            if action is not None:
                require(tokenizer.decode(payload, skip_special_tokens=False, clean_up_tokenization_spaces=False) == action,
                        "ByteLevel and tokenizer text disagree")
    if "prediction" in record:
        require(record["prediction"] == action, "prediction text differs from full emitted token IDs")
    if "valid_encoding" in record:
        require(type(record["valid_encoding"]) is bool and record["valid_encoding"] is (action is not None), "encoding flag contradicts decisions")
    if reason == "invalid_special_token":
        require(payload and (payload[-1] in added or payload[-1] >= len(tokenizer)), "special-token stop lacks a terminal actual special/unmapped token")
    if not eos:
        reasons.append("missing_eos_truncated")
    if reason == "wall_time_budget":
        reasons.append("wall_time_budget")
    if action is not None:
        if not action:
            reasons.append("empty_action")
        elif action != action.strip():
            reasons.append("outer_whitespace")
        if any(unicodedata.category(char) in REJECTED_CATEGORIES for char in action):
            reasons.append("control_format_or_multiline")
        if "<tactic>" in action or "</tactic>" in action:
            reasons.append("unexpected_completion_markup")
    return {"action": action, "valid_action": not reasons, "rejection_reasons": reasons, "eos": eos,
            "decision_tokens": len(ids), "payload_tokens": len(payload),
            "raw_bytes_hex": None if raw is None else raw.hex(), "prediction_record_sha256": object_digest(record)}


def native_source_identity(root):
    root = Path(root)
    return {str(path.relative_to(root)): digest(path)
            for base in (root / "training" / "peano_policy", root / "peano-lab" / "py" / "peano_lab")
            for path in sorted(base.rglob("*.py"))}


class PeanoRuntime:
    """Frozen constructive runtime, never a model, sampler or repair layer."""
    def __init__(self, peano_root, admission, *, expected_admission_sha256=ADMISSION_SHA256, split="val", training_rollout_collection=False):
        require_slurm()
        from .qwen_corpus import validate_admission
        self.expected_admission_sha256, self.split = expected_admission_sha256, split
        self.root = Path(peano_root).resolve()
        self.admission_path = Path(admission).resolve() if isinstance(admission, (str, Path)) else None
        if self.admission_path is not None:
            require(digest(self.admission_path) == expected_admission_sha256, "runtime admission differs from external pin")
            self.admission = decode(self.admission_path.read_text(encoding="utf-8"))
        else:
            # In-memory admission is only for a caller that already bound the
            # exact file hash; full evaluation below always supplies its path.
            self.admission = admission
        allowed = validate_admission(self.admission, expected_admission_sha256=expected_admission_sha256)
        require(type(training_rollout_collection) is bool
                and ((split in allowed - {"train"} and not training_rollout_collection)
                     or (split == "train" and split in allowed and training_rollout_collection)),
                "runtime requires an explicit evaluation split or opt-in train-only rollout collection")
        self.training_rollout_collection = training_rollout_collection
        self.before = native_source_identity(self.root)
        require(self.before == self.admission["source_files_sha256"], "native source differs from admitted checker")
        sys.dont_write_bytecode = True
        sys.path[:0] = [str(self.root / "peano-lab" / "py"), str(self.root)]
        from peano_lab import batch
        from peano_lab.ui.prove import SurfaceCapabilities, surface_success_trace_tactic, surface_failure_trace_tactics
        from peano_lab.engine.trace import TraceLimitError, render_goals
        self.batch, self.surface_class, self.trace_limit_error = batch, SurfaceCapabilities, TraceLimitError
        self.success_label, self.failure_labels = surface_success_trace_tactic, surface_failure_trace_tactics
        self.render_goals = render_goals
        self.authorities = {}
        for key, authority in self.admission["authorities"].items():
            spec = authority["capabilities"]
            caps = SurfaceCapabilities(label=spec["label"], allowed_commands=frozenset(spec["allowed_commands"]),
                                       allowed_theorems=frozenset(spec["allowed_theorems"]))
            require(batch.capability_sha256(caps) == key, "capabilities differ from admitted authority")
            self.authorities[key] = caps
        self.assert_unchanged()
        self.reference_checked = {}

    def assert_unchanged(self):
        require(native_source_identity(self.root) == self.before, "native sources changed during evaluation")
        if self.admission_path is not None:
            require(digest(self.admission_path) == self.expected_admission_sha256, "admission changed during evaluation")
        for name, module in tuple(sys.modules.items()):
            if name == "peano_lab" or name.startswith("peano_lab.") or name.startswith("training.peano_policy"):
                location = getattr(module, "__file__", None)
                require(location is not None and Path(location).resolve().is_relative_to(self.root), "imported a foreign cached Peano module")

    def initial_state(self, task):
        require(task["split"] == self.split and task["environment_sha256"] in self.authorities
                and task["library_prefix_length"] == 247 and task["focus"] == 0, "invalid proof task authority/split/focus")
        formula, names = self.batch.parse_formula_with_names(task["formula"])
        require(self.batch.pretty_formula(formula, list(names)) == task["formula"], "task formula is not canonical")
        goals = self.render_goals(self.batch.start(formula, names))
        require(goals == task["initial_state"], "autonomous root differs from admitted original target")
        return goals

    def run_prefix(self, task, actions, previous_transitions=()):
        """Replay exactly the supplied raw action list from its original target.

        Previously accepted transitions must replay identically. Native trace
        labels may normalize primitive spacing; the raw submitted strings are
        always retained separately and never changed before dispatch.
        """
        require(actions and len(previous_transitions) == len(actions) - 1, "invalid generated-prefix accounting")
        try:
            result = self.batch.run_proof(task["formula"], actions,
                                         request_id="c3-" + object_digest([task["id"], actions])[:32],
                                         classical=False, on_error="stop", capabilities=self.authorities[task["environment_sha256"]])
        except self.batch.BatchRequestError as exc:
            return {"status": "invalid_action_request", "valid_transition": False, "python_kernel_complete": False,
                    "native_error": str(exc), "native_error_type": type(exc).__name__, "transitions": list(previous_transitions), "native_result": None}
        except self.trace_limit_error as exc:
            return {"status": "native_trace_resource_limit", "valid_transition": False, "python_kernel_complete": False,
                    "native_error": str(exc), "native_error_type": type(exc).__name__, "transitions": list(previous_transitions), "native_result": None}
        require(result.status in NATIVE_STATUSES and result.classical is False and result.theorem == task["formula"]
                and result.environment_sha256 == task["environment_sha256"] and result.trace is not None,
                "native target/logic/authority/trace identity mismatch")
        steps = [step for step in result.trace if "v" in step]
        require(len(steps) == len(actions) and result.tactics_requested == len(actions), "native replay transition/request count mismatch")
        transition_keys = ("step", "goals_before", "focus", "tactic", "goals_after", "status", "error")
        for new, old in zip(steps, previous_transitions):
            require(all(new.get(key) == old.get(key) for key in transition_keys) and new["status"] == "ok", "previously accepted generated prefix changed")
        before = previous_transitions[-1]["goals_after"] if previous_transitions else self.initial_state(task)
        last = steps[-1]
        require(last["goals_before"] == before, "generated action ran in a different goal state")
        require(type(last["focus"]) is int and 0 <= last["focus"] < len(before), "native action-local focus is out of range")
        valid = last["status"] == "ok"
        if valid:
            require(last["tactic"] == self.success_label(actions[-1]), "successful trace is not bound to the raw submitted action")
            require(result.tactics_applied == len(actions) and result.failed_tactics == 0
                    and result.status in {"proved", "open", "kernel_rejection"}, "native success counters/status mismatch")
        else:
            require(last["status"] == "error" and last["tactic"] in self.failure_labels(actions[-1])
                    and result.status in {"tactic_error", "tactic_limit"}
                    and result.tactics_applied == len(actions) - 1 and result.failed_step == len(actions), "native failure not bound to final raw action")
        complete = result.status == "proved" and result.kernel_checked is True
        require(result.kernel_checked is complete and (result.status != "proved" or complete), "native QED/kernel flag mismatch")
        require(list(result.goals) == last["goals_after"], "native remaining goals differ from trace")
        if complete:
            require(valid and not result.goals and result.trace[-1].get("qed") is True, "native proof completion retains goals or lacks QED footer")
        return {"status": result.status, "valid_transition": valid, "python_kernel_complete": complete,
                "native_error": result.error, "native_error_type": result.error_type,
                "proof_nodes": result.proof_nodes, "remaining_goals": list(result.goals),
                "trace_sha256": object_digest(result.trace), "transitions": steps,
                "native_result": result.to_dict(include_trace=True)}

    def verify_reference(self, episode):
        require(episode and all(row["split"] == self.split for row in episode), "reference episode has a foreign split")
        session = episode[0]["session_id"]
        if session in self.reference_checked:
            return self.reference_checked[session]
        first = episode[0]
        task = {"id": session, "split": self.split, "formula": first["formula"], "initial_state": first["state"], "focus": 0,
                "library_prefix_length": first["library_prefix_length"], "environment_sha256": first["environment_sha256"]}
        # A single native execution, without O(n^2) gold-prefix replay.
        result = self.batch.run_proof(task["formula"], [row["completion"] for row in episode],
                                     request_id="c3-reference-" + object_digest(session)[:24], classical=False,
                                     on_error="stop", capabilities=self.authorities[task["environment_sha256"]])
        require(result.status == "proved" and result.kernel_checked is True and result.classical is False
                and result.theorem == task["formula"] and result.environment_sha256 == task["environment_sha256"]
                and result.trace is not None and result.trace[-1].get("qed") is True and not result.goals,
                "admitted reference no longer has Python-kernel-checked QED")
        steps = [step for step in result.trace if "v" in step]
        require(len(steps) == len(episode) and result.tactics_applied == len(episode) and result.failed_tactics == 0,
                "reference replay counters mismatch")
        for step, row in zip(steps, episode):
            require(step["status"] == "ok" and step["tactic"] == row["completion"]
                    and step["goals_before"] == row["state"] and step["focus"] == row["focus"], "admitted reference state/action/focus drift")
        value = {"task": task, "transitions": steps, "trace_sha256": object_digest(result.trace), "proof_nodes": result.proof_nodes}
        self.reference_checked[session] = value
        return value


def checked_budgets(budgets=None, *, ceiling=None):
    value = {**DEFAULT_BUDGETS, **(budgets or {})}
    require(set(value) == set(DEFAULT_BUDGETS) and all(type(item) is int and item > 0 for item in value.values()), "invalid finite evaluation budgets")
    require(value["candidates_per_step"] == value["search_width"] == 1, "this protocol has one greedy trajectory, no search branches")
    ceiling = DEFAULT_BUDGETS if ceiling is None else ceiling
    require(type(ceiling) is dict and set(ceiling) == set(DEFAULT_BUDGETS)
            and all(type(item) is int and item > 0 for item in ceiling.values()), "invalid registered budget ceiling")
    require(all(value[key] <= ceiling[key] for key in value), "requested evaluation exceeds registered bounds")
    return value


def effective_generation_budget(prompt, tokenizer, budgets, consumed=0):
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    require(type(prompt_ids) is list and prompt_ids, "invalid generated-state prompt encoding")
    available = budgets["max_context_tokens"] - len(prompt_ids)
    total = budgets["max_total_decision_tokens"] - consumed
    return min(budgets["max_new_tokens"], max(0, available), max(0, total)), len(prompt_ids)


def check_prompt_binding(record, prompt, tokenizer, effective_limit, max_context_tokens=None):
    require(record.get("prompt_sha256") == hashlib.sha256(prompt.encode()).hexdigest()
            and record.get("prompt_tokens") == len(tokenizer.encode(prompt, add_special_tokens=False))
            and record.get("max_new_tokens") == effective_limit, "generated decisions are not bound to the exact requested prompt/budget")
    if max_context_tokens is not None:
        require(record.get("max_context_tokens") == max_context_tokens, "callback context differs from suite protocol")


def callback_accepts_deadline(propose):
    """Inspect compatibility before a call; never retry after callback errors."""
    try:
        parameters = inspect.signature(propose).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(parameter.kind == inspect.Parameter.VAR_KEYWORD
               or (parameter.name == "deadline_monotonic"
                   and parameter.kind in {inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD})
               for parameter in parameters)


def call_propose(propose, prompt, *, max_new_tokens, deadline_monotonic=None):
    """Pass an absolute phase deadline when supported; retain legacy fixtures.

    A model callback should stop between generation steps at the earlier of its
    own event deadline and this phase deadline. An already-running model/native
    call cannot be preempted here; late completion remains a budget failure.
    """
    kwargs = {"max_new_tokens": max_new_tokens}
    if callback_accepts_deadline(propose):
        kwargs["deadline_monotonic"] = deadline_monotonic
    return propose(prompt, **kwargs)


def evaluate_action(row, episode, record, runtime, tokenizer, max_new_tokens=256, *, expected_provenance=None):
    """One generated action after a reference prefix; never autonomous pass@1."""
    require(row in episode and row["split"] == getattr(runtime, "split", "val"), "action row absent from explicit evaluation episode")
    require("id" not in record or record["id"] == row["id"], "prediction ID differs from its selected action")
    require("expected" not in record or record["expected"] == row["completion"], "prediction target differs from admission")
    if expected_provenance is not None:
        check_prompt_binding(record, row["prompt"], tokenizer, max_new_tokens)
    reference = runtime.verify_reference(episode)
    index = next(index for index, item in enumerate(episode) if item["id"] == row["id"])
    parsed = strict_generation(record, tokenizer, max_new_tokens, expected_provenance=expected_provenance)
    receipt = {"id": row["id"], "session_id": row["session_id"], "task_family": row["task_family"],
               "source_step": row["step"], "reference_prefix_length": index, "generation": record, "decoded": parsed,
               "exact_match": parsed["eos"] and parsed["action"] == row["completion"],
               "valid_transition": False, "python_kernel_completion_with_reference_prefix": False,
               "autonomous_proof_success": None, "lean_acceptance": "not-performed", "native_result": None}
    if not parsed["valid_action"]:
        receipt["status"] = "malformed_or_truncated"
        return receipt
    actions = [item["completion"] for item in episode[:index]] + [parsed["action"]]
    result = runtime.run_prefix(reference["task"], actions, reference["transitions"][:index])
    receipt.update(status=result["status"], valid_transition=result["valid_transition"],
                   python_kernel_completion_with_reference_prefix=result["python_kernel_complete"],
                   native_result=result["native_result"], native_error=result["native_error"],
                   native_error_type=result["native_error_type"])
    return receipt


def rollout(task, propose, runtime, tokenizer, budgets=None, *, expected_provenance=None, deadline_monotonic=None, budget_ceiling=None):
    """Autonomous single trajectory from the original target, with no gold actions.

    propose(prompt, *, max_new_tokens, deadline_monotonic=None) receives only the
    current all-goal compact prompt and finite token/time limits. Legacy callbacks
    without the optional deadline remain supported. No source action, future
    state, theorem label, task family or reference prefix is passed to it.
    """
    require_slurm()
    budgets = checked_budgets(budgets, ceiling=budget_ceiling)
    goals = runtime.initial_state(task)
    actions, transitions, receipts = [], [], []
    consumed, native_work = 0, 0
    result = {"id": task["id"], "session_id": task["session_id"], "task_family": task["task_family"],
              "stratum": task["stratum"], "formula": task["formula"], "environment_sha256": task["environment_sha256"],
              "task_sha256": object_digest(task), "budgets": budgets, "status": "action_budget",
              "autonomous_python_kernel_proof": False, "lean_acceptance": "not-performed",
              "reference_actions_used": 0, "search_branches": 1, "restarts": 0,
              "actions": actions, "steps": receipts, "native_result": None}
    for index in range(budgets["max_actions"]):
        if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
            result["status"] = "not_attempted_deadline" if not receipts else "deadline"
            break
        prompt = compact_prompt(goals, task["library_prefix_length"], focus=0)
        limit, prompt_length = effective_generation_budget(prompt, tokenizer, budgets, consumed)
        if limit <= 0:
            result["status"] = "context_limit" if prompt_length >= budgets["max_context_tokens"] else "total_token_budget"
            break
        if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
            result["status"] = "not_attempted_deadline" if not receipts else "deadline"
            break
        raw = call_propose(propose, prompt, max_new_tokens=limit, deadline_monotonic=deadline_monotonic)
        if expected_provenance is not None:
            check_prompt_binding(raw, prompt, tokenizer, limit, budgets["max_context_tokens"])
        parsed = strict_generation(raw, tokenizer, limit, expected_provenance=expected_provenance)
        consumed += parsed["decision_tokens"]
        step = {"index": index + 1, "prompt": prompt, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "prompt_tokens": prompt_length, "effective_max_new_tokens": limit, "generation": raw, "decoded": parsed}
        receipts.append(step)
        if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
            result["status"] = "deadline_after_model_call"
            break
        if not parsed["valid_action"]:
            result["status"] = "malformed_or_truncated"
            break
        actions.append(parsed["action"])
        native = runtime.run_prefix(task, actions, transitions)
        native_work += len(actions)
        step.update(status=native["status"], valid_transition=native["valid_transition"],
                    native_error=native["native_error"], native_error_type=native["native_error_type"],
                    trace_sha256=native.get("trace_sha256"))
        result["native_result"] = native["native_result"]
        if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
            result["status"] = "deadline_after_native_call"
            result["native_completion_outside_wall_budget"] = native["python_kernel_complete"]
            break
        if not native["valid_transition"]:
            result["status"] = native["status"]
            break
        transitions = native["transitions"]
        goals = native["remaining_goals"]
        if native["python_kernel_complete"]:
            result.update(status="proved", autonomous_python_kernel_proof=True, proof_nodes=native["proof_nodes"])
            break
        if native["status"] == "kernel_rejection":
            result["status"] = "kernel_rejection"
            break
        require(goals, "open proof has no goals")
    result.update(model_calls=len(receipts), generated_decision_tokens=consumed,
                  submitted_actions=len(actions), accepted_actions=len(transitions),
                  native_prefix_transitions_requested=native_work, remaining_goals=goals,
                  wall_budget_limited="deadline" in result["status"] or any(step["generation"]["stop_reason"] == "wall_time_budget" for step in receipts))
    return result


def _suite_inputs(prepared_dir, admission_path, peano_root, tokenizer, provenance, extra_input_hashes=None,
                  *, split="val", expected_admission_sha256=ADMISSION_SHA256, expected_preparation_sha256=None):
    from .qwen_corpus import prepared_inputs
    prepared_dir = Path(prepared_dir)
    manifest, selection, rows, metadata, before = prepared_inputs(prepared_dir, split=split,
        expected_admission_sha256=expected_admission_sha256, expected_preparation_sha256=expected_preparation_sha256)
    require(selection is not None, "evaluation cannot use the training split")
    require(digest(admission_path) == expected_admission_sha256, "evaluation admission differs from external pin")
    files = [Path(admission_path), Path(__file__), Path(sys.modules[compact_prompt.__module__].__file__),
             Path(sys.modules[prepared_inputs.__module__].__file__)]
    before.update({str(path.resolve()): digest(path) for path in files})
    for path, checksum in (extra_input_hashes or {}).items():
        require(digest(path) == checksum, "extra prediction/provenance input changed before evaluation")
        before[str(Path(path).resolve())] = checksum
    by_id, episodes = {row["id"]: row for row in rows}, group_sessions(rows)
    require(all(key in by_id for key in selection["generation_ids"])
            and len(set(selection["generation_ids"])) == len(selection["generation_ids"]) == selection["generation_rows"], "invalid selected generation IDs")
    require(len(selection["proof_tasks"]) == selection["proof_tasks_count"]
            and [task["id"] for task in selection["proof_tasks"]] == selection["proof_task_ids"]
            and len(set(selection["proof_task_ids"])) == len(selection["proof_tasks"]), "invalid proof task selection")
    excluded = {by_id[key]["session_id"] for key in selection["generation_ids"]}
    for task in selection["proof_tasks"]:
        require(task["session_id"] == task["id"] and task["id"] in episodes and task["id"] not in excluded, "proof task is not disjoint admitted validation")
        episode = episodes[task["id"]]
        require(task["source_row_ids"] == [row["id"] for row in episode]
                and task["admitted_episode_sha256"] == object_digest([{key: row[key] for key in sorted(ROW_FIELDS)} for row in episode]), "proof task episode binding mismatch")
        first = episode[0]
        require(all(task[key] == first[key] for key in ("formula", "environment_sha256", "library_prefix_length", "focus", "task_family"))
                and task["initial_state"] == first["state"] and task["split"] == split, "proof task changed original target/state/split")
        if metadata is not None:
            from .qwen_corpus import task_from_episode
            require(task == task_from_episode(episode, metadata[task["session_id"]]), "proof task structural metadata changed")
    validate_provenance(provenance)
    actual_tokenizer = tokenizer_identity(tokenizer)
    # Actual files were verified by the pinned loader. Reconstruct the identity
    # hash with that flag, while independently binding the live backend/vocab.
    actual_tokenizer["file_bytes_verified"] = True
    require(actual_tokenizer == manifest["tokenizer"]
            and object_digest(actual_tokenizer) == provenance["tokenizer_identity_sha256"], "live tokenizer differs from prepared inputs/provenance")
    runtime = PeanoRuntime(peano_root, admission_path, expected_admission_sha256=expected_admission_sha256, split=split)
    runtime.task_metadata = metadata
    require(runtime.before == manifest["peano_source_files_sha256"]
            and runtime.admission["authorities"] == manifest["authorities"], "prepared/native checker or authority identities differ")
    return manifest, selection, by_id, episodes, runtime, before


def stratified_results(output_dir, by_id, selection, metadata, *, run_rollouts=True):
    """Aggregate saved complete rosters; receipt failures stay in denominators."""
    buckets = {}
    proof_by_id = {task["id"]: task for task in selection["proof_tasks"]}
    for scope, filename in (("action", "actions.jsonl"), ("proof", "proofs.jsonl")):
        observed = []
        with (Path(output_dir) / filename).open("rb") as stream:
            for raw in stream:
                require(raw.endswith(b"\n"), "incomplete saved evaluation receipt")
                receipt = decode(raw)
                observed.append(receipt["id"])
                source = by_id[receipt["id"]] if scope == "action" else proof_by_id[receipt["id"]]
                info = metadata[source["session_id"]]
                key = (source["task_family"], info["evaluation_regime"], info["difficulty_stratum"])
                if key not in buckets:
                    buckets[key] = {"task_family": key[0], "evaluation_regime": key[1], "difficulty_stratum": key[2],
                        "action_counts": Counter(), "proof_counts": Counter(), "generation_ids": [], "proof_task_ids": []}
                bucket = buckets[key]
                counts = bucket[scope + "_counts"]
                counts["selected"] += 1
                attempted = "generation" in receipt if scope == "action" else receipt["model_calls"] > 0
                counts["attempted"] += int(attempted)
                limited = "deadline" in receipt["status"] or receipt.get("wall_budget_limited", False)
                if scope == "action" and "generation" in receipt:
                    limited |= receipt["generation"]["stop_reason"] == "wall_time_budget"
                counts["completed"] += int(attempted and not limited)
                counts["wall_budget_limited"] += int(limited)
                counts["status:" + receipt["status"]] += 1
                fields = ("exact_match", "valid_transition", "python_kernel_completion_with_reference_prefix") if scope == "action" else ("autonomous_python_kernel_proof",)
                for field in fields:
                    counts[field] += int(receipt[field])
                bucket["generation_ids" if scope == "action" else "proof_task_ids"].append(receipt["id"])
        expected = selection["generation_ids"] if scope == "action" else (selection["proof_task_ids"] if run_rollouts else [])
        require(observed == expected and len(observed) == len(set(observed)), "saved receipts are not the complete ordered frozen roster")
    result = []
    for key in sorted(buckets):
        bucket = buckets[key]
        actions, proofs = bucket["action_counts"], bucket["proof_counts"]
        bucket["action_yields_all_selected"] = {field: actions[field] / actions["selected"] if actions["attempted"] else None
            for field in ("exact_match", "valid_transition", "python_kernel_completion_with_reference_prefix")}
        bucket["proof_yield_all_selected"] = proofs["autonomous_python_kernel_proof"] / proofs["selected"] if proofs["attempted"] else None
        bucket["action_counts"], bucket["proof_counts"] = dict(actions), dict(proofs)
        result.append(bucket)
    return result


def evaluate_suite(prepared_dir, admission_path, peano_root, tokenizer, propose, provenance, output_dir,
                   budgets=None, *, predictions=None, run_rollouts=True, max_wall_seconds=1800, extra_input_hashes=None,
                   split="val", expected_admission_sha256=ADMISSION_SHA256, expected_preparation_sha256=None,
                   budget_ceiling=None, wall_seconds_ceiling=3600, selection_usage=None, proof_task_limit=None):
    """Run complete frozen validation selections and persist per-task receipts.

    Optional predictions is a complete ordered generation-ID list; each record
    has id plus the strict generation fields. When supplied, propose is only
    used for autonomous tasks. Never accept an arbitrary successful subset.
    With rollouts enabled, actions may consume at most the first half of the
    suite wall budget. Proofs can use all time remaining until its global end.
    Callbacks that declare deadline_monotonic receive the appropriate deadline;
    legacy callbacks retain cooperative checks only around complete calls.
    """
    require_slurm()
    selection_usage = ("development-model-selection" if split in {"val", "dev"} else "held-out-evaluation") if selection_usage is None else selection_usage
    require(selection_usage in {"development-model-selection", "held-out-evaluation", "frozen-checkpoint-comparison"}
            and not (split == "test" and selection_usage == "development-model-selection"), "invalid evaluation selection role")
    budgets = checked_budgets(budgets, ceiling=budget_ceiling)
    output_dir = Path(output_dir)
    require(not output_dir.resolve().is_relative_to(Path(peano_root).resolve()), "never write into native Peano source")
    output_dir.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    require(type(wall_seconds_ceiling) in {int, float} and math.isfinite(wall_seconds_ceiling) and 0 < wall_seconds_ceiling
            and type(max_wall_seconds) in {int, float} and math.isfinite(max_wall_seconds)
            and 0 < max_wall_seconds <= wall_seconds_ceiling, "invalid evaluation wall budget")
    deadline = started + max_wall_seconds
    action_seconds = max_wall_seconds / 2 if run_rollouts else max_wall_seconds
    action_deadline = started + action_seconds
    callback_has_deadline = callable(propose) and callback_accepts_deadline(propose)
    provenance_hash = object_digest(provenance)
    predictions_hash = None if predictions is None else object_digest(predictions)
    try:
        manifest, selection, by_id, episodes, runtime, before = _suite_inputs(prepared_dir, admission_path, peano_root, tokenizer, provenance, extra_input_hashes,
            split=split, expected_admission_sha256=expected_admission_sha256, expected_preparation_sha256=expected_preparation_sha256)
        projection = None
        if proof_task_limit is not None:
            require(split == "dev" and selection_usage == "development-model-selection"
                    and type(proof_task_limit) is int and 0 < proof_task_limit <= len(selection["proof_tasks"]),
                    "online proof projection must be a nonempty fixed development prefix")
            projection = {"rule": "ordered-prefix-v1", "source_selection_object_sha256": object_digest(selection),
                          "source_proof_task_count": len(selection["proof_tasks"]), "selected_count": proof_task_limit}
            selection = {**selection, "proof_tasks": selection["proof_tasks"][:proof_task_limit],
                "proof_task_ids": selection["proof_task_ids"][:proof_task_limit], "proof_tasks_count": proof_task_limit}
        if predictions is not None:
            require(type(predictions) is list and [item.get("id") for item in predictions] == selection["generation_ids"], "predictions are not the complete ordered frozen generation selection")
        require(callable(propose) or (predictions is not None and not run_rollouts), "missing model callback")
        action_counts, proof_counts = Counter(), Counter()
        action_counts["selected"] = len(selection["generation_ids"])
        proof_counts["selected"] = len(selection["proof_tasks"]) if run_rollouts else 0
        with (output_dir / "actions.jsonl").open("x", encoding="utf-8") as stream:
            for index, key in enumerate(selection["generation_ids"]):
                row = by_id[key]
                if time.monotonic() >= action_deadline:
                    receipt = {"id": key, "session_id": row["session_id"], "status": "not_attempted_deadline",
                               "exact_match": False, "valid_transition": False, "python_kernel_completion_with_reference_prefix": False,
                               "autonomous_proof_success": None, "lean_acceptance": "not-performed"}
                    stream.write(canonical(receipt) + "\n")
                    stream.flush()
                    action_counts["status:not_attempted_deadline"] += 1
                    action_counts["wall_budget_limited"] += 1
                    continue
                limit, prompt_length = effective_generation_budget(row["prompt"], tokenizer, budgets)
                require(limit > 0, "admitted selected action has no generation context; revise protocol before use")
                if time.monotonic() >= action_deadline:
                    receipt = {"id": key, "session_id": row["session_id"], "status": "not_attempted_deadline",
                               "exact_match": False, "valid_transition": False, "python_kernel_completion_with_reference_prefix": False,
                               "autonomous_proof_success": None, "lean_acceptance": "not-performed"}
                    stream.write(canonical(receipt) + "\n")
                    stream.flush()
                    action_counts["status:not_attempted_deadline"] += 1
                    action_counts["wall_budget_limited"] += 1
                    continue
                raw = predictions[index] if predictions is not None else call_propose(propose, row["prompt"], max_new_tokens=limit, deadline_monotonic=action_deadline)
                check_prompt_binding(raw, row["prompt"], tokenizer, limit, budgets["max_context_tokens"])
                if time.monotonic() >= action_deadline:
                    parsed = strict_generation(raw, tokenizer, limit, expected_provenance=provenance)
                    receipt = {"id": key, "session_id": row["session_id"], "status": "deadline_after_model_call", "generation": raw, "decoded": parsed,
                               "exact_match": False, "valid_transition": False, "python_kernel_completion_with_reference_prefix": False,
                               "autonomous_proof_success": None, "lean_acceptance": "not-performed"}
                else:
                    receipt = evaluate_action(row, episodes[row["session_id"]], raw, runtime, tokenizer, limit, expected_provenance=provenance)
                    if time.monotonic() >= action_deadline:
                        receipt.update(status="deadline_after_native_call", completion_outside_wall_budget=receipt["python_kernel_completion_with_reference_prefix"],
                                       exact_match=False, valid_transition=False, python_kernel_completion_with_reference_prefix=False)
                receipt.update(prompt_tokens=prompt_length, effective_max_new_tokens=limit)
                stream.write(canonical(receipt) + "\n")
                stream.flush()
                action_counts["attempted"] += 1
                for field in ("exact_match", "valid_transition", "python_kernel_completion_with_reference_prefix"):
                    action_counts[field] += int(receipt[field])
                action_counts["status:" + receipt["status"]] += 1
                action_counts["wall_budget_limited"] += int("deadline" in receipt["status"] or raw["stop_reason"] == "wall_time_budget")
                print(canonical({"event": "qwen-native-action", "completed": index + 1, "total": len(selection["generation_ids"])}), flush=True)
        actions_finished = time.monotonic()
        with (output_dir / "proofs.jsonl").open("x", encoding="utf-8") as stream:
            if run_rollouts:
                for task in selection["proof_tasks"]:
                    # Native reference replay is an infrastructure check only.
                    # Its actions never enter rollout()/the callback.
                    if time.monotonic() < deadline:
                        runtime.verify_reference(episodes[task["session_id"]])
                    receipt = rollout(task, propose, runtime, tokenizer, budgets, expected_provenance=provenance, deadline_monotonic=deadline, budget_ceiling=budget_ceiling)
                    stream.write(canonical(receipt) + "\n")
                    stream.flush()
                    proof_counts["attempted"] += int(receipt["model_calls"] > 0)
                    proof_counts["recorded"] += 1
                    proof_counts["autonomous_python_kernel_proof"] += int(receipt["autonomous_python_kernel_proof"])
                    proof_counts["status:" + receipt["status"]] += 1
                    proof_counts["wall_budget_limited"] += int(receipt["wall_budget_limited"])
                    print(canonical({"event": "qwen-autonomous-proof", "recorded": proof_counts["recorded"], "total": len(selection["proof_tasks"])}), flush=True)
        proofs_finished = time.monotonic()
        runtime.assert_unchanged()
        require(all(digest(path) == value for path, value in before.items()), "evaluation source/data inputs changed")
        require(object_digest(provenance) == provenance_hash and (predictions is None or object_digest(predictions) == predictions_hash), "in-memory generator provenance/predictions changed")
        summary = {"format": FORMAT, "status": "budget_limited" if action_counts["wall_budget_limited"] or proof_counts["wall_budget_limited"] else "completed", "tier": "T4", "split": split,
                   "slurm_job_id": os.environ["SLURM_JOB_ID"], "provenance": provenance, "budgets": budgets,
                   "action_counts": dict(action_counts), "proof_counts": dict(proof_counts),
                   "generation_ids": selection["generation_ids"], "proof_task_ids": selection["proof_task_ids"] if run_rollouts else [],
                   "autonomous_rollouts_performed": run_rollouts, "test_parsed": split == "test", "validation_used_for_selection": selection_usage == "development-model-selection",
                   "selection_usage": selection_usage,
                   "lean_acceptance": "not-performed", "python_kernel_scope": "native Peano constructive checker, classical=False, frozen model-v3 capabilities",
                   "generation_provenance_scope": "callback declares the checkpoint/source/policy identity; retained actual decisions and native results bind the evaluated behavior",
                   "max_wall_seconds": max_wall_seconds, "deadline_scope": "cooperative checks around model/native calls; an individual call can finish after deadline and is then a budget failure; SLURM provides the hard process deadline",
                   "wall_time_allocation": {"policy": "actions-first-half-proofs-remaining-v1" if run_rollouts else "actions-only-v1",
                       "action_deadline_seconds_from_start": action_seconds,
                       "proof_reserved_seconds": max_wall_seconds - action_seconds if run_rollouts else 0,
                       "proof_global_deadline_seconds_from_start": max_wall_seconds if run_rollouts else None,
                       "actions_finished_seconds_from_start": actions_finished - started,
                       "proof_phase_elapsed_seconds": proofs_finished - actions_finished,
                       "callback_deadline_keyword_supported": callback_has_deadline,
                       "legacy_callback_scope": None if callback_has_deadline else "reservation cannot preempt a legacy callback already in progress"},
                   "proof_success_rate_all_selected": None if not run_rollouts else proof_counts["autonomous_python_kernel_proof"] / proof_counts["selected"],
                   "action_rates_all_selected": {field: action_counts[field] / action_counts["selected"] for field in ("exact_match", "valid_transition", "python_kernel_completion_with_reference_prefix")},
                   "provenance_object_sha256": provenance_hash, "predictions_object_sha256": predictions_hash,
                   "elapsed_seconds": time.monotonic() - started, "input_sha256_before_and_after": before,
                   "native_source_files_sha256": runtime.before, "actions_sha256": digest(output_dir / "actions.jsonl"),
                   "proofs_sha256": digest(output_dir / "proofs.jsonl"), "python": {"version": sys.version, "executable": sys.executable}}
        if projection is not None:
            summary["proof_roster_projection"] = projection
        summary["evaluation_contract"] = {"dataset_id": manifest.get("dataset_id", "campaign2-admitted-compact-state"),
            "split": split, "preparation_sha256": digest(Path(prepared_dir) / "preparation.json"),
            "admission_sha256": expected_admission_sha256,
            "selection_object_sha256": object_digest(selection),
            "ordered_roster_sha256": object_digest({"generation_ids": selection["generation_ids"], "proof_task_ids": summary["proof_task_ids"]}),
            "authority_inventory_sha256": object_digest(manifest["authorities"]),
            "task_metadata_sha256": manifest.get("task_metadata", {}).get(split, {}).get("sha256"),
            "budgets": budgets, "max_wall_seconds": max_wall_seconds,
            "budget_ceiling": DEFAULT_BUDGETS if budget_ceiling is None else budget_ceiling,
            "wall_seconds_ceiling": wall_seconds_ceiling}
        if getattr(runtime, "task_metadata", None) is not None:
            summary["stratified_results"] = stratified_results(output_dir, by_id, selection, runtime.task_metadata, run_rollouts=run_rollouts)
            summary["proof_success_rate_all_selected"] = (proof_counts["autonomous_python_kernel_proof"] / proof_counts["selected"]
                if run_rollouts and proof_counts["attempted"] else None)
            summary["action_rates_all_selected"] = {field: action_counts[field] / action_counts["selected"] if action_counts["attempted"] else None
                for field in ("exact_match", "valid_transition", "python_kernel_completion_with_reference_prefix")}
            summary["coverage_semantics"] = "selected includes every frozen target; attempted requires a model call; completed excludes wall-deadline-limited attempts; zero attempts yields null"
        write_json(output_dir / "summary.json", summary)
        return summary
    except Exception as exc:
        write_json(output_dir / "FAILED.json", {"format": FORMAT, "status": "infrastructure-abort", "summary_valid": False,
                   "error_type": type(exc).__name__, "error": str(exc), "slurm_job_id": os.environ["SLURM_JOB_ID"]})
        raise


def main():
    parser = argparse.ArgumentParser(description="Check a complete validation generation JSON array; autonomous rollouts use evaluate_suite's callback API.")
    parser.add_argument("--prepared-dir", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--peano-root", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    require_slurm()
    before = {str(path.resolve()): digest(path) for path in (args.predictions, args.provenance)}
    tokenizer, _ = load_pinned_tokenizer(args.tokenizer_path)
    predictions = decode(args.predictions.read_text(encoding="utf-8"))
    provenance = decode(args.provenance.read_text(encoding="utf-8"))
    summary = evaluate_suite(args.prepared_dir, args.admission, args.peano_root, tokenizer, None, provenance,
                             args.output_dir, predictions=predictions, run_rollouts=False, extra_input_hashes=before)
    require(all(digest(path) == value for path, value in before.items()), "prediction/provenance inputs changed")
    write_json(args.output_dir / "cli-inputs.json", {"input_sha256_before_and_after": before,
               "summary_sha256": digest(args.output_dir / "summary.json"), "status": summary["status"]})


if __name__ == "__main__":
    main()
