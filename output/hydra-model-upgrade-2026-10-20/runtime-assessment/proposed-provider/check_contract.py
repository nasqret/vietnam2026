"""Pure contract fixtures: no Torch, Transformers, native execution or network.

Exercises the actual receipt decoder/compact renderer from the supplied frozen
source directory. This is not a model quality or numerical backend test.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
from hydra_torch_candidate import CandidatePolicy, Limits, EXECUTION_COMMANDS, BindingError


class Tokenizer:
    eos_token_id = 256
    all_special_ids = [256]

    def __init__(self, inverse):
        self.byte_chars = {value: key for key, value in inverse.items()}

    def __len__(self):
        return 257

    def encode(self, value, *, add_special_tokens):
        assert add_special_tokens is False
        return list(value.encode())

    def decode(self, ids, *, skip_special_tokens, clean_up_tokenization_spaces):
        assert skip_special_tokens is False and clean_up_tokenization_spaces is False
        return bytes(ids).decode()

    def convert_ids_to_tokens(self, ids):
        return [self.byte_chars[token] for token in ids]

    def get_added_vocab(self):
        return {"<eos>": 256}


class Backend:
    kind = "latent_compact_v3"
    model_vocab_size = 257

    def __init__(self, ids, *, fail=False, time_advance=None):
        self.ids, self.fail, self.time_advance = iter(ids), fail, time_advance

    def next_token(self, sequence, allowed_ids, *, forward_started, forward_completed):
        assert allowed_ids is None or all(type(t) is int for t in allowed_ids)
        forward_started()
        if self.fail:
            raise RuntimeError("fixture forward failure")
        token = next(self.ids)
        if allowed_ids is not None:
            assert token in allowed_ids
        forward_completed()
        if self.time_advance:
            self.time_advance()
        return token, {"depth": 1, "block_calls": 28, "head_calls": 1, "gate_calls": 0, "readouts": 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-source", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.frozen_source.resolve() / "src"))
    strict = importlib.import_module("latentproof.qwen_eval")
    data = importlib.import_module("latentproof.qwen_data")
    tokenizer = Tokenizer(strict.byte_decoder())
    environment = SimpleNamespace(prompt_version=4, classical=False, library=(),
        capabilities=SimpleNamespace(label="hydra-authority-no-imports-v1",
                                     allowed_commands=EXECUTION_COMMANDS, allowed_theorems=()))
    provenance = {"checkpoint_sha256": "a" * 64, "tokenizer_identity_sha256": "b" * 64,
                  "source_inventory_sha256": "c" * 64, "run_id": "pure-fixture-not-a-model",
                  "policy": {"kind": "fixed", "depth": 1}, "model_vocab_size": 257}
    authority_calls = []

    def validator(action, env):
        # Deliberately a fake authority callback. No native claim is made.
        authority_calls.append(action)
        assert env is environment
        if action not in ("refl", "assumption"):
            raise ValueError("fixture refuses other tactics")
        return action

    def make(text="refl", *, eos=True, backend=None, **options):
        backend = backend or Backend(list(text.encode()) + ([256] if eos else []))
        return CandidatePolicy(backend=backend, tokenizer=tokenizer, kind=backend.kind,
            environment=environment, provenance=provenance, render_prompt=data.compact_prompt,
            strict_generation=strict.strict_generation, check_prompt_binding=strict.check_prompt_binding,
            validate_tactic=validator, **options)

    names = []

    policy = make()
    assert policy.propose(("⊢ 0 = 0",), max_candidates=4) == ("refl",)
    report = policy.report()
    assert report["actual_model_calls"] == 1 and report["forward_attempts"] == 5
    assert report["forward_passes"] == 5 and report["generated_token_slots"] == 5
    assert report["attempts"][0]["generation"]["decision_ids"] == [114, 101, 102, 108, 256]
    assert report["kernel_checked"] is False and report["identity"]["max_candidates"] == 1
    assert report["identity"]["conditioning_authority"] != report["identity"]["execution_authority"]
    report["attempts"][0]["generation"]["decision_ids"].clear()
    assert len(policy.report()["attempts"][0]["generation"]["decision_ids"]) == 5
    names.append("literal one-candidate EOS receipt and isolated reports")

    before = len(authority_calls)
    for action in (" refl", "refl\n", "refl\nassumption", "<tactic>refl</tactic>", ""):
        assert make(action).propose(("⊢ 0 = 0",), max_candidates=4) == ()
    assert len(authority_calls) == before
    names.append("whitespace multiline markup and empty completions are not repaired")

    for action in ("use nat_add_comm", "assumption; refl"):
        policy = make(action)
        assert policy.propose(("⊢ 0 = 0",), max_candidates=4) == ()
        assert policy.report()["attempts"][0]["candidate_count"] == 0
    names.append("library imports and failed authority checks cannot become candidates")

    policy = make("refl", eos=False, limits=Limits(max_new_tokens=4))
    assert policy.propose(("⊢ 0 = 0",), max_candidates=1) == ()
    assert "missing_eos_truncated" in policy.report()["attempts"][0]["rejection_reasons"]
    assert policy.calls == 1 and policy.generated_tokens == 4
    names.append("token exhaustion without actual EOS is rejected")

    policy = make(limits=Limits(max_context_tokens=2))
    assert policy.propose(("⊢ 0 = 0",), max_candidates=4) == ()
    assert policy.calls == policy.forward_attempts == policy.generated_tokens == 0
    names.append("overlong prompt is refused without truncation or model credit")

    policy = make(backend=Backend([], fail=True))
    try:
        policy.propose(("⊢ 0 = 0",), max_candidates=4)
        raise AssertionError("fixture forward error hidden")
    except RuntimeError:
        pass
    assert policy.calls == policy.forward_attempts == 1
    assert policy.forward_passes == policy.generated_tokens == 0
    assert policy.report()["attempts"][0]["status"] == "failed"
    names.append("failed forward is charged as an attempted call, with no invented tokens")

    now = [0.0]
    backend = Backend([256], time_advance=lambda: now.__setitem__(0, 31.0))
    policy = make(backend=backend, clock=lambda: now[0])
    try:
        policy.propose(("⊢ 0 = 0",), max_candidates=4)
        raise AssertionError("late EOS accepted")
    except TimeoutError:
        pass
    assert policy.calls == policy.forward_passes == policy.generated_tokens == 1
    assert policy.report()["attempts"][0]["candidate_count"] == 0
    names.append("late actual EOS stays counted but cannot be accepted")

    policy = make(should_stop=lambda: True)
    try:
        policy.propose(("⊢ 0 = 0",), max_candidates=4)
        raise AssertionError("stop request ignored")
    except TimeoutError:
        pass
    assert policy.calls == 0
    names.append("pre-forward cancellation spends no model call")

    checked_prompt = data.compact_prompt(["⊢ 0 = 0"], library_prefix_length=247, focus=0)
    assert checked_prompt == 'HA model-v3 library-prefix=247/247\n{"focus":0,"goals":["⊢ 0 = 0"]}\nTactic:'
    policy = make()
    policy.propose(("⊢ 0 = 0",), max_candidates=4)
    receipt = policy.report()["attempts"][0]["generation"]
    try:
        strict.check_prompt_binding(receipt, checked_prompt + " ", tokenizer, 128, max_context_tokens=6144)
        raise AssertionError("prompt drift accepted")
    except data.IntegrityError:
        pass
    receipt["provenance"]["checkpoint_sha256"] = "d" * 64
    try:
        strict.strict_generation(receipt, tokenizer, 128, expected_provenance=provenance)
        raise AssertionError("checkpoint drift accepted")
    except data.IntegrityError:
        pass
    names.append("actual frozen decoder rejects prompt and checkpoint receipt drift")

    backend = Backend([114, 101, 102, 108, 256])
    backend.kind = "historical_primitive_v4"
    seen = []

    def constraint_factory(tok, env, *, prompt_length, max_new_tokens):
        assert tok is tokenizer and env is environment and max_new_tokens == 128
        def constraint(batch, prefix):
            seen.append(prefix.tolist())
            return list(range(len(tok)))
        return constraint

    def primitive_prompt(*, goals, focus, environment):
        assert goals == ("⊢ 0 = 0",) and focus == 0
        return "fixture-primitive-prompt"

    policy = CandidatePolicy(backend=backend, tokenizer=tokenizer, kind=backend.kind,
        environment=environment, provenance=provenance, render_prompt=primitive_prompt,
        strict_generation=strict.strict_generation, check_prompt_binding=strict.check_prompt_binding,
        validate_tactic=validator, constraint_factory=constraint_factory)
    assert policy.propose(("⊢ 0 = 0",), max_candidates=4) == ("refl",)
    assert len(seen) == 5 and seen[-1][-4:] == [114, 101, 102, 108]
    names.append("historical renderer and prefix mask are used at every token step")

    prohibited = [name for name in sys.modules if name.split(".")[0] in
                  {"torch", "transformers", "peft", "mlx", "peano_lab", "training"}]
    assert not prohibited, prohibited
    print(json.dumps({"format": "hydra-provider-pure-contract-fixtures-v1", "passed": True,
        "checks": names, "forbidden_framework_or_native_imports": prohibited,
        "real_model_calls": 0, "native_proof_calls": 0, "numerical_backend_tested": False}, indent=2))


if __name__ == "__main__":
    main()
