"""Actual local tokenizer CPU parity; model frameworks and weight reads denied."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.environ.update(USE_TORCH="0", USE_TF="0", USE_FLAX="0", HF_HUB_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
sys.path.insert(0, str(HERE))
from cached_tokenizer_length import ImmutableTokenizerLength


def guard(event, args):
    if event == "import" and str(args[0]).split(".")[0] in {"mlx", "mlx_lm", "torch", "tensorflow", "jax"}:
        raise RuntimeError("Model framework import forbidden in CPU tokenizer test")
    if event.startswith("socket."):
        raise RuntimeError("Network forbidden in CPU tokenizer test")
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        name = os.fsdecode(args[0])
        if name.endswith((".safetensors", ".pt", ".bin")):
            raise RuntimeError("Model weight reads forbidden in CPU tokenizer test")


sys.addaudithook(guard)
from transformers import AutoTokenizer

FROZEN = ROOT / "output/hydra-model-upgrade-2026-10-20/comparison-01/latent-source/src/latentproof"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


data = module("compact_qwen_data", FROZEN / "qwen_data.py")
evaluation = module("compact_qwen_eval", FROZEN / "qwen_eval.py")
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(SOURCE), str(SOURCE / "peano-lab/py")]
from training.peano_policy.authority import AuthorityTokenConstraint
from training.peano_policy.contract import authority_prompt_environment
from training.peano_policy.prompt import CapabilityIdentity
from peano_lab.batch import MODEL_V1_COMMANDS

CASE = ROOT / "output/hydra-wmi-integration-2026-10-21/evaluation/newest-01/primary-01.json"
CASE_SHA = "60e258cd5d81ea445e950d35972b1f3d496509a587f1264a0142954b278e828f"
STEPS = (0, 12, 24, 35)
EVIDENCE = []


class Prefix(list):
    def tolist(self):
        return list(self)


class TokenizerParity(unittest.TestCase):
    def test_actual_both_tokenizers_exact_read_and_mask_parity(self):
        raw = CASE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), CASE_SHA)
        saved = json.loads(raw)
        trace = [row for row in saved["result"]["last_native_result"]["trace"] if "tactic" in row]
        prompts = [data.compact_prompt(trace[i]["goals_before"]) for i in STEPS]
        for i, prompt in zip(STEPS, prompts):
            self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(), saved["provider"]["attempts"][i]["prompt_sha256"])
        environment = authority_prompt_environment(False, CapabilityIdentity(
            label="hydra-playground-native-v1", allowed_commands=tuple(sorted(MODEL_V1_COMMANDS)), allowed_theorems=()))
        directories = {"historical": ROOT / "artifacts/hydra-retention-pilot-2026-08-30/trained-model-collected-01/model/tokenizer",
                       "newest": ROOT / "hydra-playground/.runtime/model"}
        for name, directory in directories.items():
            with self.subTest(tokenizer=name):
                before_files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()
                                if p.is_file() and p.name in {"tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
                                                             "added_tokens.json", "vocab.json", "merges.txt"}}
                original = AutoTokenizer.from_pretrained(str(directory), trust_remote_code=False,
                                                        use_fast=True, local_files_only=True)
                wrapper = ImmutableTokenizerLength(original)
                self.assertEqual(len(wrapper), len(original))
                self.assertEqual(wrapper.get_vocab(), original.get_vocab())
                self.assertEqual(wrapper.get_added_vocab(), original.get_added_vocab())
                self.assertEqual(wrapper.backend_tokenizer.to_str(), original.backend_tokenizer.to_str())
                self.assertEqual(wrapper.backend_tokenizer.decoder.__getstate__(), original.backend_tokenizer.decoder.__getstate__())
                self.assertEqual(data.tokenizer_identity(wrapper), data.tokenizer_identity(original))
                for prompt, i in zip(prompts, STEPS):
                    ids = original.encode(prompt, add_special_tokens=False)
                    self.assertEqual(wrapper.encode(prompt, add_special_tokens=False), ids)
                    for kwargs in ({"skip_special_tokens": False, "clean_up_tokenization_spaces": False},
                                   {"skip_special_tokens": True, "clean_up_tokenization_spaces": False}):
                        self.assertEqual(wrapper.decode(ids, **kwargs), original.decode(ids, **kwargs))
                    self.assertEqual(wrapper.convert_ids_to_tokens(ids), original.convert_ids_to_tokens(ids))
                    generation = saved["provider"]["attempts"][i]["generation"]
                    self.assertEqual(evaluation.strict_generation(generation, wrapper, generation["max_new_tokens"]),
                                     evaluation.strict_generation(generation, original, generation["max_new_tokens"]))
                # Check actual authority masks, including empty, partial head,
                # argument and completed-head prefixes. Same256? No shortcuts:
                # each original/wrapped151k vocabulary is genuinely inspected.
                masks = []
                for tokenizer in (original, wrapper):
                    constraint = AuthorityTokenConstraint(tokenizer, environment, prompt_length=1, max_new_tokens=128)
                    masks.append([constraint(0, Prefix([0] + tokenizer.encode(prefix, add_special_tokens=False)))
                                  for prefix in ("", "intro", "intro x", "refl")])
                self.assertEqual(masks[0], masks[1])
                length = len(original)
                start = time.monotonic()
                for _ in range(5000):
                    self.assertEqual(len(wrapper), length)
                fast_seconds = time.monotonic() - start
                custody = wrapper.verify_unchanged()
                self.assertEqual(custody["custody_status"], "verified")
                for mutation in (lambda: setattr(wrapper, "eos_token_id", 0),
                                 lambda: setattr(wrapper.backend_tokenizer, "decoder", None)):
                    with self.assertRaises(TypeError):
                        mutation()
                for mutator in ("add_tokens", "add_special_tokens", "train_new_from_iterator", "_tokenizer"):
                    with self.assertRaises(AttributeError):
                        getattr(wrapper, mutator)
                with self.assertRaises(AttributeError):
                    wrapper.backend_tokenizer.add_tokens(["forbidden"])
                after_files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()
                               if p.is_file() and p.name in before_files}
                self.assertEqual(before_files, after_files)
                EVIDENCE.append({"tokenizer": name, "files": before_files, "custody": custody,
                    "fixed_prompt_trace_indices": list(STEPS), "full_vocab_equal": True, "identity_equal": True,
                    "encode_decode_equal": True, "strict_generation_equal": True, "authority_masks_equal": True,
                    "cached_length_5000_reads_seconds": fast_seconds})
                # A retained external reference must not evade final custody.
                original.add_tokens(["hydra-cpu-mutation-detection-fixture"])
                with self.assertRaises(ValueError):
                    wrapper.verify_unchanged()
                # No tokenizer is written back to disk or used for inference.


if __name__ == "__main__":
    started = time.monotonic()
    outcome = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TokenizerParity))
    print(json.dumps({"schema": "hydra-cached-tokenizer-cpu-parity-v1", "passed": outcome.wasSuccessful(),
                      "model_inference": False, "model_frameworks_loaded": [k for k in sys.modules if k.split('.')[0] in {"mlx", "mlx_lm", "torch"}],
                      "case_sha256": CASE_SHA, "tokenizers": EVIDENCE, "seconds": time.monotonic() - started}), flush=True)
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
