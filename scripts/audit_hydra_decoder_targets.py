#!/usr/bin/env python3
"""Check frozen Hydra SFT targets against its real tokenizer and token mask.

This is a tokenizer-only check, not a native replay, model-quality evaluation,
or permission to train. It never changes the dataset or decoder limits.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import importlib.machinery
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, limit=16 * 1024**2):
    require(path.is_file() and not path.is_symlink(), "Expected an ordinary input file: " + str(path))
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "Input exceeds its byte limit")
    return raw


class _Ids:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return list(self.values)


class _NoModelOrNative:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"torch", "tensorflow", "jax", "mlx", "peano_lab"}:
            # Library availability probes may inspect specs without importing.
            # Block execution, rather than mistaking that metadata read for it.
            actual = importlib.machinery.PathFinder.find_spec(fullname, path)
            if actual is not None:
                return importlib.machinery.ModuleSpec(fullname, self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        raise RuntimeError("Tokenizer-only audit forbids this import: " + module.__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-bundle", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--dataset-relative", required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--model-admission", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "Output already exists; preserve the previous audit")
    resource.setrlimit(resource.RLIMIT_CPU, (90, 100))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(120)
    began = time.monotonic()
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", USE_TORCH="0",
                      USE_TF="0", USE_FLAX="0", TOKENIZERS_PARALLELISM="false")
    source = args.source_bundle / "source"
    manifest_raw = read(args.source_bundle / "manifest.json", 1024**2)
    require(digest(manifest_raw) == args.manifest_sha256, "Frozen source manifest changed")
    manifest = json.loads(manifest_raw)
    pins = {}

    def source_read(relative):
        path = Path(relative)
        require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == relative,
                "Source input must be an exact relative path")
        raw = read(source / relative)
        pin = {"bytes": len(raw), "sha256": digest(raw)}
        require(manifest["files"].get(relative) == pin, "Frozen source input changed: " + relative)
        pins[relative] = pin
        return raw

    training = "hydra-playground/training-v5/"
    package = training + "hydra_training_v5/"
    for name in ("__init__.py", "peano_policy/__init__.py", "peano_policy/prompt.py",
                 "peano_policy/library_identity.py", "peano_policy/authority.py"):
        source_read(package + name)
    provider = ast.parse(source_read("hydra-playground/experimental_model.py"))
    constants = {}
    for node in provider.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in {"MAX_INPUT_TOKENS", "MAX_PRIMITIVE_TOKENS"}:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
    require(constants == {"MAX_INPUT_TOKENS": 4096, "MAX_PRIMITIVE_TOKENS": 64},
            "This audit supports the explicit 4096-input / 64-output primitive profile")
    admission_raw = read(args.model_admission, 1024**2)
    admission = json.loads(admission_raw)
    require(admission["model_loaded"] is True and admission["adapter"]["saved_adapter_reload_checked"] is True,
            "Use the existing actual saved-model admission to identify the tokenizer")
    versions = {name: importlib.metadata.version(name) for name in ("transformers", "tokenizers")}
    require(all(versions[name] == admission["frameworks"][name] for name in versions),
            "Tokenizer runtime versions differ from the actual model admission")
    tokenizer_pins = {}
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json"):
        raw = read(args.tokenizer / name)
        pin = {"bytes": len(raw), "sha256": digest(raw)}
        require(pin == admission["base_files"][name], "Tokenizer metadata differs from the actual loaded model")
        tokenizer_pins[name] = pin

    def no_external_action(event, details):
        if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.posix_spawn"}:
            raise RuntimeError("Tokenizer-only audit forbids network/subprocess activity: " + event)

    sys.addaudithook(no_external_action)
    sys.meta_path.insert(0, _NoModelOrNative())
    sys.path.insert(0, str(source / training))
    from transformers import AutoTokenizer
    from hydra_training_v5.peano_policy.authority import AuthorityTokenConstraint
    from hydra_training_v5.peano_policy.prompt import (
        CapabilityIdentity, PromptEnvironment, parse_prompt, validate_completion,
    )
    tokenizer = AutoTokenizer.from_pretrained(str(args.tokenizer), local_files_only=True, trust_remote_code=False)
    require(type(tokenizer.eos_token_id) is int, "Tokenizer does not define a single EOS")
    constraints, target_cache = {}, {}
    splits = {}
    all_row_ids = set()
    for split in ("train", "val"):
        relative = args.dataset_relative.rstrip("/") + "/primitive-" + split + ".jsonl"
        dataset_raw = source_read(relative)
        lines = dataset_raw.splitlines()
        require(0 < len(lines) <= 10000, "Dataset row count is outside the finite audit scope")
        heads, failures, maxima = Counter(), [], {"prompt_tokens": 0, "target_tokens_including_eos": 0}
        sequence_digest = hashlib.sha256()
        for line_number, raw in enumerate(lines, 1):
            require(len(raw) <= 1024**2, "Dataset line is oversized")
            row = json.loads(raw)
            require(row["schema"] == "hydra-primitive-sft-v1" and row["split"] == split
                    and row["prompt_version"] == 4 and row["kernel_checked"] is True
                    and row["censored"] is False, "Row does not have the selected primitive SFT shape")
            require(row["id"] not in all_row_ids, "Duplicate row id across training/validation")
            all_row_ids.add(row["id"])
            parsed = parse_prompt(row["prompt"])
            caps = row["capabilities"]
            capabilities = CapabilityIdentity(caps["label"], tuple(caps["allowed_commands"]), tuple(caps["allowed_theorems"]))
            environment = PromptEnvironment(parsed.classical, capabilities, prompt_version=4)
            require(parsed.prompt_version == 4 and parsed.focus == row["focus"] == 0
                    and parsed.goals == tuple(row["goals_before"])
                    and parsed.environment_sha256 == row["environment_sha256"] == environment.sha256
                    and parsed.allowed_command_names == capabilities.allowed_commands
                    and parsed.allowed_theorem_names == capabilities.allowed_theorems,
                    "Stored prompt and action authority disagree")
            tactic = validate_completion(row["completion"])
            require(tactic == row["action"], "Stored action and supervised suffix disagree")
            head = tactic.split()[0]
            heads[head] += 1
            prompt_ids = tokenizer.encode(row["prompt"], add_special_tokens=False)
            key = (environment, tactic)
            if key not in target_cache:
                ids = tokenizer.encode(tactic, add_special_tokens=False) + [tokenizer.eos_token_id]
                if environment not in constraints:
                    constraints[environment] = AuthorityTokenConstraint(tokenizer, environment,
                                                                        prompt_length=0, max_new_tokens=64)
                mask_error = None
                for position, token in enumerate(ids):
                    if position >= 64:
                        break
                    try:
                        allowed = constraints[environment](0, _Ids(ids[:position]))
                        if token not in allowed:
                            mask_error = {"position": position, "token_id": token, "reason": "gold token is masked"}
                            break
                    except (ValueError, RuntimeError) as error:
                        mask_error = {"position": position, "token_id": token, "reason": str(error)}
                        break
                target_cache[key] = (ids, mask_error)
            ids, mask_error = target_cache[key]
            reasons = []
            if len(ids) > 64:
                reasons.append("target exceeds 64 generated tokens including EOS")
            if len(prompt_ids) > 4096 or len(prompt_ids) + len(ids) > 4096:
                reasons.append("full training sequence exceeds 4096 tokens")
            if len(tactic.encode()) > 512:
                reasons.append("target exceeds provider command-byte limit")
            if mask_error is not None:
                reasons.append("gold token path is unreachable under the authority mask")
            if reasons:
                failures.append({"id": row["id"], "line": line_number, "head": head, "action": tactic,
                                 "target_tokens_including_eos": len(ids), "reasons": reasons, "mask_failure": mask_error})
            maxima["prompt_tokens"] = max(maxima["prompt_tokens"], len(prompt_ids))
            maxima["target_tokens_including_eos"] = max(maxima["target_tokens_including_eos"], len(ids))
            sequence_digest.update(json.dumps([row["id"], prompt_ids, ids], separators=(",", ":")).encode() + b"\n")
        splits[split] = {"rows": len(lines), "compatible_rows": len(lines) - len(failures),
                         "incompatible_rows": len(failures), "action_heads": dict(sorted(heads.items())),
                         "maxima": maxima, "tokenized_rows_sha256": sequence_digest.hexdigest(), "failures": failures}
    require(not any(name.split(".")[0] in {"torch", "tensorflow", "jax", "mlx", "peano_lab"} for name in sys.modules),
            "A model or native module was imported")
    for relative, expected in pins.items():
        raw = read(source / relative)
        require({"bytes": len(raw), "sha256": digest(raw)} == expected, "Source input changed during audit")
    for name, expected in tokenizer_pins.items():
        raw = read(args.tokenizer / name)
        require({"bytes": len(raw), "sha256": digest(raw)} == expected, "Tokenizer changed during audit")
    compatible = all(value["incompatible_rows"] == 0 for value in splits.values())
    report = {"schema": "hydra-tokenizer-only-target-audit-v1", "completed": True, "compatible": compatible,
              "source_manifest_sha256": args.manifest_sha256, "source_inputs": pins,
              "model_id": admission["model_id"], "actual_model_admission_sha256": digest(admission_raw),
              "tokenizer_inputs": tokenizer_pins, "runtime_versions": versions, "limits": constants,
              "unique_action_authority_pairs": len(target_cache), "splits": splits,
              "training_heads_absent_from_validation": sorted(set(splits["train"]["action_heads"]) - set(splits["val"]["action_heads"])),
              "validation_scope": "gold-token reachability and lengths only; no argument execution or proof-quality claim",
              "dataset_admitted_for_training": False, "dataset_or_model_modified": False,
              "model_loads": 0, "native_runs": 0, "gpu_allocations": 0, "network_operations": 0,
              "elapsed_seconds": time.monotonic() - began}
    output = (json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    require(len(output) <= 1024**2, "Audit report exceeds its bound")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(output)
    signal.alarm(0)
    print(json.dumps({"output": str(args.output), "compatible": compatible, "bytes": len(output),
                      "sha256": digest(output), "splits": {key: {field: value[field] for field in
                      ("rows", "compatible_rows", "incompatible_rows", "maxima")} for key, value in splits.items()},
                      "elapsed_seconds": report["elapsed_seconds"]}))
    return 0 if compatible else 2


if __name__ == "__main__":
    raise SystemExit(main())
