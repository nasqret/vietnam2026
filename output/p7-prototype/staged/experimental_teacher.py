"""One pinned remote teacher; every returned plan remains untrusted.

This module does not download, allocate, retry, train, or execute native proofs.
Its exact read-only P6 helper dependency supplies file and reservation checks;
the frozen Qwen registry/provider are never enlarged or modified. Frameworks
are imported only after authenticating an explicitly supplied owned GH200 job.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys


PROFILE = "hydra-remote-deepseek-teacher-v1"
PROMPT_VERSION = "hydra-deepseek-native-json-teacher-input-v1"
REGISTRY_SHA256 = "a56dad7ac6368964c039c9ddabab5ac6174939f9684ae23bf6872080cf38c105"
HELPER_SHA256 = "b5b85ed8bba6b0e6cdda4c7772443c5fec630a5643deba7d53598bcdd0cf9598"
REGISTRY_PATH = Path(__file__).resolve().parent / "experimental-models/deepseek-teacher-v1.json"
MODEL_KEY = "deepseek-prover-v2-7b-teacher"
MODEL_ID = "deepseek-ai/DeepSeek-Prover-V2-7B"
REVISION = "a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b"
MAX_INPUT_TOKENS = 4096
MAX_OUTPUT_TOKENS = 512
MAX_CALLS = 64
MAX_GENERATED_TOKENS = MAX_CALLS * MAX_OUTPUT_TOKENS
_LOADED = object()
_EXAMPLE = ('{"v":1,"plans":[{"reason":"Introduce the next universally quantified variable.",'
            '"actions":[{"kind":"step","tactic":"intro","name":"n"}]}]}')
_PREFIX = ("Native PA teacher interface " + PROMPT_VERSION + ".\n"
    "Return only the JSON plan document specified below. All auxiliary statements remain obligations. "
    "Do not emit Lean, imports, code fences, a proof claim, or explanatory text outside JSON.\n"
    "This is a syntax-only example of one action; it is not an answer to the supplied goal:\n" + _EXAMPLE + "\n"
    "Choose actions from the actual goal and authority below, rather than copying the example.\n\n")


class TeacherAdmissionError(ValueError):
    pass


class TeacherCancelled(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise TeacherAdmissionError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def stopped(should_stop):
    if should_stop is not None and should_stop():
        raise TeacherCancelled("The host stopped the bounded teacher operation.")


def _helpers(app_root):
    """Read-only use of exact reviewed generic P6 I/O; not its model allowlist."""
    root = Path(app_root or Path(__file__).resolve().parent).resolve(strict=True)
    path = root / "experimental_model.py"
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 128 * 1024
            and sha256(path.read_bytes()).hexdigest() == HELPER_SHA256,
            "Teacher requires the exact unchanged P6 file/reservation helper.")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    helper = importlib.import_module("experimental_model")
    require(Path(helper.__file__).resolve() == path, "Wrong P6 helper module path.")
    return helper


def registry(*, app_root=None):
    helper = _helpers(app_root)
    descriptor, raw, _ = helper._file(REGISTRY_PATH, maximum=65536, read=True)
    require(descriptor["sha256"] == REGISTRY_SHA256, "Teacher registry bytes changed.")
    value = helper._json(raw)
    require(value.get("schema") == "hydra-experimental-teacher-registry-v1"
            and value.get("model_key") == MODEL_KEY and value.get("model_id") == MODEL_ID
            and value.get("revision") == REVISION and value.get("teacher_adapters_allowed") is False,
            "Only the one exact unadapted teacher is admitted.")
    return value


def _identity(files):
    value = {"schema": "hydra-authenticated-teacher-base-v1", "model_key": MODEL_KEY,
        "model_id": MODEL_ID, "revision": REVISION, "registry_sha256": REGISTRY_SHA256,
        "files": files, "model_loaded": False, "weight_bytes_fully_hashed": True}
    value["base_identity_sha256"] = sha256(canonical(value)).hexdigest()
    return value


def authenticate_teacher(base_directory, *, app_root=None, should_stop=None):
    require(should_stop is None or callable(should_stop), "Invalid cancellation callback.")
    helper = _helpers(app_root)
    spec = registry(app_root=app_root)
    _, files, watched = helper._base_files(base_directory, spec, should_stop)
    helper._unchanged(watched)
    return _identity(files)


def metadata_status(*, app_root=None):
    spec = registry(app_root=app_root)
    return {"profile": PROFILE, "model_key": MODEL_KEY, "model_id": MODEL_ID, "revision": REVISION,
        "declared_weight_bytes": sum(x["bytes"] for x in spec["weight_files"].values()),
        "architecture": "LlamaForCausalLM", "available": False, "model_loaded": False,
        "local_loading_supported": False, "automatic_download": False, "native_json_quality_tested": False}


@dataclass(frozen=True)
class TeacherLimits:
    max_calls: int = MAX_CALLS
    max_generated_tokens: int = MAX_GENERATED_TOKENS

    def __post_init__(self):
        require(type(self.max_calls) is int and 1 <= self.max_calls <= MAX_CALLS
                and type(self.max_generated_tokens) is int
                and 1 <= self.max_generated_tokens <= MAX_GENERATED_TOKENS,
                "Teacher budget exceeds the 32-state campaign ceiling.")


def validate_loaded_config(observed, spec):
    """Only Transformers' documented legacy RoPE key addition is permitted."""
    require(type(observed) is dict, "Loaded configuration is not a record.")
    for key, expected in spec["config"].items():
        if key in {"transformers_version", "use_cache"}:
            continue
        if key == "rope_scaling":
            expected = dict(expected)
            expected["rope_type"] = expected["type"]
        require(observed.get(key) == expected, "Loaded teacher architecture differs: " + key)
    return True


def load_teacher(base_directory, *, reservation_check, app_root=None, should_stop=None,
                 limits=TeacherLimits(), seed=20260904):
    require(callable(reservation_check) and (should_stop is None or callable(should_stop))
            and type(limits) is TeacherLimits and type(seed) is int and 0 <= seed < 2**32,
            "Explicit live reservation, finite limits and seed are required.")
    require(platform.system() == "Linux" and platform.machine() == "aarch64"
            and sys.version_info[:3] == (3, 13, 5),
            "Teacher loading is remote Linux/aarch64 Python 3.13.5 only.")
    helper = _helpers(app_root)
    spec = registry(app_root=app_root)
    allocation = helper._reservation(reservation_check())

    def boundary():
        stopped(should_stop)
        require(helper._reservation(reservation_check()) == allocation, "Owned teacher allocation changed.")

    boundary()
    versions = {name: importlib.metadata.version(name) for name in spec["dependencies"]}
    require(versions == spec["dependencies"], "Pinned remote teacher dependency identities differ.")
    path, files, watched = helper._base_files(base_directory, spec, should_stop)
    base = _identity(files)
    boundary()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    require(torch.cuda.is_available() and torch.cuda.device_count() == 1 and torch.cuda.is_bf16_supported(),
            "Exactly one BF16 CUDA device is required, without CPU/MLX fallback.")
    device = torch.cuda.get_device_properties(0)
    require(device.major == 9 and "GH200" in device.name, "This teacher needs the reviewed GH200 device.")
    torch.set_num_threads(allocation["cpus"])
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True,
        use_fast=True, trust_remote_code=False)
    _, tokenizer_raw, _ = helper._file((path / "tokenizer_config.json").resolve(strict=True),
        maximum=spec["metadata_files"]["tokenizer_config.json"]["bytes"],
        expected=spec["metadata_files"]["tokenizer_config.json"], read=True)
    tokenizer_config = helper._json(tokenizer_raw)
    require(type(tokenizer).__name__ == spec["tokenizer_class"] and tokenizer.is_fast
            and 0 < len(tokenizer) <= spec["config"]["vocab_size"]
            and tokenizer.bos_token_id == spec["config"]["bos_token_id"]
            and tokenizer.eos_token_id == spec["config"]["eos_token_id"]
            and tokenizer.pad_token_id == tokenizer.eos_token_id
            and tokenizer.chat_template == tokenizer_config["chat_template"],
            "Loaded teacher tokenizer or chat template differs from the pinned metadata.")
    tokenizer.padding_side = "right"
    boundary()
    model = AutoModelForCausalLM.from_pretrained(str(path), local_files_only=True,
        trust_remote_code=False, use_safetensors=True, torch_dtype=torch.bfloat16,
        attn_implementation="sdpa", device_map={"": "cuda:0"})
    require(type(model).__name__ == "LlamaForCausalLM"
            and type(model).__module__ == "transformers.models.llama.modeling_llama",
            "Teacher loaded an unexpected implementation.")
    validate_loaded_config(model.config.to_dict(), spec)
    require(sum(p.numel() for p in model.parameters()) == spec["declared_parameter_count"]
            and all(p.dtype == torch.bfloat16 and p.device.type == "cuda" for p in model.parameters()),
            "Loaded teacher parameter population/dtype/device differs.")
    model.eval()
    model.requires_grad_(False)
    model.config.use_cache = True
    boundary()
    helper._unchanged(watched)
    tokenizer_identity = sha256(canonical({name: files[name]
        for name in ("tokenizer.json", "tokenizer_config.json")})).hexdigest()
    identity = {"schema": "hydra-loaded-remote-teacher-v1", "profile": PROFILE,
        "model_key": MODEL_KEY, "model_id": MODEL_ID, "revision": REVISION,
        "registry_sha256": REGISTRY_SHA256, "base": base, "architecture": spec["config"],
        "frameworks": versions, "backend": spec["inference_backend"],
        "tokenizer_sha256": tokenizer_identity,
        "chat_template_sha256": sha256(tokenizer.chat_template.encode()).hexdigest(),
        "prompt_contract": PROMPT_VERSION, "seed": seed, "allocation": allocation,
        "device": device.name, "model_loaded": True, "adapter_present": False,
        "kernel_checked": False, "automatic_download": False, "automatic_retry": False,
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "p6_helper_sha256": HELPER_SHA256}
    identity["model_manifest_sha256"] = sha256(canonical(identity)).hexdigest()
    return TeacherSession(_LOADED, model, tokenizer, torch, identity, limits, boundary, should_stop)


class TokenLedger:
    """Actual greedy decode tokens, including an EOS or a cancelled last step."""
    def __init__(self, prompt_length, maximum, account, should_stop):
        self.prompt_length, self.maximum = prompt_length, maximum
        self.account, self.should_stop, self.seen = account, should_stop, 0

    def observe(self, rows, columns):
        count = columns - self.prompt_length
        require(type(rows) is int and rows == 1 and type(columns) is int
                and self.seen <= count <= self.maximum, "Unexpected teacher token population.")
        self.account(count - self.seen)
        self.seen = count
        stopped(self.should_stop)
        return False

    def __call__(self, input_ids, scores, **kwargs):
        return self.observe(int(input_ids.shape[0]), int(input_ids.shape[1]))


class TeacherSession:
    def __init__(self, permit, model, tokenizer, torch, identity, limits, boundary, should_stop):
        require(permit is _LOADED, "Only the authenticated teacher loader can construct a session.")
        self.model, self.tokenizer, self.torch, self.identity = model, tokenizer, torch, identity
        self.limits, self.boundary, self.should_stop = limits, boundary, should_stop
        self.calls = self.generated_tokens = self.forward_passes = 0
        self._busy = False

    def encode_prompt(self, prompt):
        require(type(prompt) is str and 0 < len(prompt.encode()) <= 128 * 1024,
                "Full teacher prompt exceeds its byte bound; no truncation.")
        stopped(self.should_stop)
        text = _PREFIX + prompt
        messages = [{"role": "user", "content": text}]
        tokens = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
        require(type(tokens) is list and all(type(t) is int and 0 <= t < 102400 for t in tokens),
                "Teacher tokenizer returned malformed IDs.")
        return text, tuple(tokens)

    def generate(self, input_ids, *, maximum, tracker, should_stop=None):
        require(type(input_ids) is tuple and 0 < len(input_ids) <= MAX_INPUT_TOKENS
                and all(type(t) is int and 0 <= t < 102400 for t in input_ids),
                "The entire templated teacher input must fit 4096 tokens.")
        require(type(maximum) is int and 1 <= maximum <= MAX_OUTPUT_TOKENS
                and not self._busy and self.calls < self.limits.max_calls
                and self.generated_tokens + maximum <= self.limits.max_generated_tokens,
                "Shared teacher call/token budget exhausted or concurrent generation attempted.")

        def stop():
            return bool((self.should_stop and self.should_stop()) or (should_stop and should_stop()))

        stopped(stop)
        self.boundary()
        torch = self.torch
        from transformers import GenerationConfig, StoppingCriteriaList
        encoded = torch.tensor([list(input_ids)], dtype=torch.long, device="cuda:0")
        attention = torch.ones_like(encoded)

        def account(count):
            self.generated_tokens += count
            tracker.generated_tokens += count

        ledger = TokenLedger(len(input_ids), maximum, account, stop)
        config = GenerationConfig(max_new_tokens=maximum, do_sample=False, num_beams=1,
            num_return_sequences=1, bos_token_id=self.tokenizer.bos_token_id,
            eos_token_id=self.tokenizer.eos_token_id, pad_token_id=self.tokenizer.pad_token_id,
            use_cache=True, return_dict_in_generate=False, output_scores=False,
            output_attentions=False, output_hidden_states=False)

        def forward_hook(module, inputs):
            self.forward_passes += 1

        hook = self.model.register_forward_pre_hook(forward_hook)
        self._busy = True
        try:
            stopped(stop)
            self.calls += 1
            tracker.calls += 1
            with torch.inference_mode():
                output = self.model.generate(input_ids=encoded, attention_mask=attention,
                    generation_config=config, stopping_criteria=StoppingCriteriaList([ledger]))
            require(len(output.shape) == 2 and output.shape[0] == 1
                    and len(input_ids) < output.shape[1] <= len(input_ids) + maximum,
                    "Teacher decoder returned unexpected sequence dimensions.")
            row = output[0].tolist()
            require(tuple(row[:len(input_ids)]) == input_ids, "Teacher decoder changed its input prefix.")
            suffix = tuple(row[len(input_ids):])
            require(ledger.seen == len(suffix), "Actual teacher decode token accounting differs.")
            stopped(stop)
            return suffix
        finally:
            self._busy = False
            hook.remove()

    def report(self):
        return {"identity": self.identity, "actual_model_calls": self.calls,
            "generated_tokens": self.generated_tokens, "forward_passes": self.forward_passes,
            "limits": {"max_calls": self.limits.max_calls,
                       "max_generated_tokens": self.limits.max_generated_tokens},
            "kernel_checked": False, "token_count_includes_cancelled_attempts": True}


class TeacherPlannerBackend:
    """Actual model backend for the unchanged finite PlannerProvider protocol."""
    def __init__(self, session):
        require(type(session) is TeacherSession and session.identity.get("model_loaded") is True,
                "Teacher backend requires the real authenticated session.")
        from planner_provider import PlannerBackendIdentity
        self.session = session
        self.identity = PlannerBackendIdentity(
            name=MODEL_KEY, architecture="LlamaForCausalLM",
            model_manifest_sha256=session.identity["model_manifest_sha256"],
            tokenizer_sha256=session.identity["tokenizer_sha256"],
            runtime_identity=PROFILE + ";" + PROMPT_VERSION)
        self.calls = self.generated_tokens = 0
        self.last_input = self.last_output = None

    def encode_prompt(self, prompt):
        from proof_planner import PlannerCancelled
        try:
            text, tokens = self.session.encode_prompt(prompt)
        except TeacherCancelled as error:
            raise PlannerCancelled(str(error)) from error
        self.last_input = {"p4_prompt": prompt, "teacher_message": text,
            "prompt_contract": PROMPT_VERSION, "input_token_ids": tokens,
            "input_tokens": len(tokens), "chat_template_sha256": self.session.identity["chat_template_sha256"]}
        self.last_output = None
        return tokens

    def generate(self, input_ids, *, max_new_tokens, should_stop=None):
        from proof_planner import PlannerCancelled
        try:
            ids = self.session.generate(input_ids, maximum=max_new_tokens, tracker=self, should_stop=should_stop)
        except TeacherCancelled as error:
            raise PlannerCancelled(str(error)) from error
        self.last_output = {"output_token_ids": ids, "decoded_text": None}
        return ids

    def decode_output(self, output_ids):
        require(type(output_ids) is tuple and 0 < len(output_ids) <= MAX_OUTPUT_TOKENS
                and all(type(t) is int and 0 <= t < 102400 for t in output_ids),
                "Malformed bounded teacher output IDs.")
        text = self.session.tokenizer.decode(output_ids, skip_special_tokens=True,
                                              clean_up_tokenization_spaces=False)
        require(type(text) is str and len(text.encode()) <= 32768, "Teacher output text exceeds its bound.")
        self.last_output = {"output_token_ids": output_ids, "decoded_text": text}
        return text
