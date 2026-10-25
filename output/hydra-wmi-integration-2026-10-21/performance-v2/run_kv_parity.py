"""PREPARED ONLY: bounded serial full-prefix versus per-tactic KV parity.

This standalone experiment is never imported by deployment or the comparison.
It loads one authenticated newest model, uses the same cached-length tokenizer
for both paths, and compares four precommitted saved-state prompts. No proof is
claimed; no runtime/default is activated, even if every token agrees.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

WHOLE_SECONDS = 900.0
PROMPT_SECONDS = 300.0
PATH_SECONDS = 30.0
MAX_TOKENS = 16
MAX_RSS_BYTES = 8 * 1024**3
PHASE_LIMITS = {"load": 120.0, "prompt": PROMPT_SECONDS, "finalize": 60.0}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "Expected a regular pinned file")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return {"bytes": size, "sha256": digest.hexdigest()}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode()


def save(directory, name, value):
    raw = json_bytes(value)
    with (directory / name).open("xb") as stream:
        stream.write(raw)
    return {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read_spec(path, checksum):
    require(pin(path)["sha256"] == checksum, "Parity spec changed")
    value = json.loads(Path(path).read_text())
    require(value["schema"] == "hydra-proposed-kv-parity-spec-v1"
            and value["limits"] == {"whole_seconds": WHOLE_SECONDS, "prompt_seconds": PROMPT_SECONDS,
                                      "provider_seconds": PATH_SECONDS, "max_new_tokens": MAX_TOKENS,
                                      "max_context_tokens": 6144, "max_rss_bytes": MAX_RSS_BYTES},
            "Parity scope/budgets changed")
    require(value["trace_indices"] == [0, 12, 24, 35] and value["automatic_retry"] is False
            and value["automatic_activation"] is False, "Unexpected selection/retry policy")
    for row in value["files"]:
        require(pin(row["path"]) == {key: row[key] for key in ("bytes", "sha256")},
                "Pinned parity input/source changed: " + row["path"])
    require(any(Path(row["path"]).resolve() == Path(__file__).resolve() for row in value["files"]),
            "Harness is not included in source pins")
    return value


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "Cannot load pinned module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class RecordingMX:
    """Observe the genuine backend's eval output; never add a forward pass."""
    def __init__(self, original):
        self.original = original
        self.last_logits = None
        self.eval_seconds = 0.0

    def __getattr__(self, name):
        return getattr(self.original, name)

    def eval(self, *args, **kwargs):
        started = time.monotonic()
        try:
            result = self.original.eval(*args, **kwargs)
            if args:
                self.last_logits = args[0]
            return result
        finally:
            self.eval_seconds += time.monotonic() - started


class RecordingBackend:
    def __init__(self, backend, observed_mx, *, cached):
        self.backend, self.mx, self.cached = backend, observed_mx, cached
        self.kind, self.model_vocab_size = backend.kind, backend.model_vocab_size
        self.rows, self.logits = [], []

    def next_token(self, sequence, allowed_ids, **callbacks):
        started = time.monotonic()
        self.mx.last_logits = None
        before_eval = self.mx.eval_seconds
        row = {"sequence_tokens": len(sequence),
               "sequence_ids_sha256": hashlib.sha256(json.dumps(sequence, separators=(",", ":")).encode()).hexdigest(),
               "decision_id": None, "completed_backend_call": False}
        try:
            token, metadata = self.backend.next_token(sequence, allowed_ids, **callbacks)
            row.update(decision_id=token, completed_backend_call=True)
            return token, metadata
        except BaseException as exc:
            row.update(error_type=type(exc).__name__, error=str(exc)[:500])
            raise
        finally:
            row.update(backend_seconds=time.monotonic() - started,
                       eval_seconds=self.mx.eval_seconds - before_eval,
                       completed_logits_eval=self.mx.last_logits is not None)
            self.rows.append(row)
            self.logits.append(self.mx.last_logits)


def run_path(template, goals, backend, observed_mx, *, cached, deadline):
    from wmi_candidate_core import CandidatePolicy, Limits
    observed = RecordingBackend(backend, observed_mx, cached=cached)
    policy = CandidatePolicy(backend=observed, tokenizer=template.tokenizer, kind=template.kind,
        environment=template.environment, provenance=template.provenance,
        render_prompt=template.render_prompt, strict_generation=template.strict_generation,
        check_prompt_binding=template.check_prompt_binding, validate_tactic=template.validate_tactic,
        constraint_factory=template.constraint_factory,
        limits=Limits(max_calls=1, max_new_tokens=MAX_TOKENS, max_total_decision_tokens=MAX_TOKENS,
                      max_context_tokens=6144, provider_seconds=PATH_SECONDS), deadline_monotonic=deadline)
    policy.evaluation_identity.update(use_cache=cached,
        backend="proposed-per-tactic-kv" if cached else "authenticated-full-prefix-reference",
        tokenizer_length_policy="hydra-immutable-tokenizer-length-v1", experiment="parity-only-not-activated")
    started = time.monotonic()
    error = None
    proposals = ()
    try:
        proposals = policy.propose(tuple(goals), max_candidates=1)
    except Exception as exc:
        error = {"type": type(exc).__name__, "message": str(exc)[:1000]}
    report = policy.report()
    forward_positions = sum((row["sequence_tokens"] if not cached or i == 0 else 1)
                            for i, row in enumerate(observed.rows) if row["completed_logits_eval"])
    return {"path": "cached" if cached else "reference", "seconds": time.monotonic() - started,
            "error": error, "proposals": list(proposals), "provider": report,
            "completed_forward_input_positions": forward_positions, "forwards": observed.rows,
            "backend_cache": backend.report() if cached else None}, observed.logits


def compare(reference, cached, ref_logits, cache_logits, mx):
    ref_attempt = reference["provider"]["attempts"][0]
    cache_attempt = cached["provider"]["attempts"][0]
    ref_ids, cache_ids = ref_attempt["decision_ids"], cache_attempt["decision_ids"]
    decisions_equal = ref_ids == cache_ids
    strict_equal = ref_attempt.get("strict_generation") == cache_attempt.get("strict_generation")
    comparisons = []
    for i, (left, right) in enumerate(zip(ref_logits, cache_logits)):
        lr, rr = reference["forwards"][i], cached["forwards"][i]
        same_prefix = lr["sequence_ids_sha256"] == rr["sequence_ids_sha256"]
        row = {"decision_index": i, "same_input_prefix": same_prefix,
               "reference_decision": lr["decision_id"], "cached_decision": rr["decision_id"]}
        for name, logits in (("reference", left), ("cached", right)):
            if logits is not None:
                top_two = mx.sort(logits[0])[-2:].tolist()
                row[name + "_top_two_logits_ascending"] = top_two
                row[name + "_top_two_margin"] = top_two[1] - top_two[0]
        row["max_absolute_logit_error"] = (float(mx.max(mx.abs(left - right)).item())
            if same_prefix and left is not None and right is not None else None)
        comparisons.append(row)
    complete = (reference["error"] is None and cached["error"] is None
                and reference["provider"]["actual_model_calls"] == cached["provider"]["actual_model_calls"] == 1
                and ref_attempt["status"] in {"suggested", "rejected"}
                and cache_attempt["status"] in {"suggested", "rejected"})
    numeric = [row["max_absolute_logit_error"] for row in comparisons]
    return {"complete_paths": complete, "exact_decision_ids_equal": decisions_equal,
            "reference_decision_ids": ref_ids, "cached_decision_ids": cache_ids,
            "exact_strict_generation_equal": strict_equal,
            "exact_proposal_equal": reference["proposals"] == cached["proposals"],
            "reference_eos": ref_attempt.get("generation", {}).get("eos"),
            "cached_eos": cache_attempt.get("generation", {}).get("eos"),
            "per_decision": comparisons,
            "max_absolute_logit_error_same_prefix_only": max((x for x in numeric if x is not None), default=None),
            "bitwise_logits_equal": bool(numeric) and all(x == 0 for x in numeric),
            "token_gate_passed": complete and decisions_equal and strict_equal
                                 and reference["proposals"] == cached["proposals"]}


def child(args):
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == "darwin",
            "Use existing isolated Mac runtime Python -I -B")
    spec = read_spec(args.spec, args.spec_sha256)
    out = Path(args.output).resolve()
    require(out.is_dir(), "Parent must create new result directory")
    repo = Path(spec["repo_root"])
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(repo / "hydra-playground"), str(Path(__file__).resolve().parent)]
    def guard(event, values):
        if event.startswith(("socket.", "subprocess.")) or event in {"os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"}:
            raise PermissionError("Parity child is offline and cannot launch processes")
        if event == "open" and isinstance(values[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(values[0])).resolve()
            if path.name in {"PRIVATE_EXPECTATIONS.json", "proofs.jsonl", "PANEL_COMMITMENT.json"}:
                raise PermissionError("Parity child cannot read private proof/selection evidence")
            mode, flags = values[1:3]
            writing = isinstance(mode, str) and any(c in mode for c in "wax+") or isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            if writing and not path.is_relative_to(out):
                raise PermissionError("Parity child cannot write outside its new evidence directory")
    sys.addaudithook(guard)
    def emit(value):
        print(json.dumps(value, allow_nan=False), flush=True)
    started = time.monotonic()
    whole_deadline = started + WHOLE_SECONDS
    shared = None
    results = []
    receipt = {"schema": "hydra-proposed-kv-parity-result-v1", "status": "started",
               "spec_sha256": args.spec_sha256, "model_quality_claim": False, "activated": False}
    try:
        from sequential_native import NativeHost
        from cached_tokenizer_length import ImmutableTokenizerLength
        from cached_mlx_backend import PerTacticKVBackend
        native = NativeHost(spec["native_source_root"])
        provider = load_module("hydra_parity_newest_provider", spec["provider_entrypoint"])
        shared = provider.NewestWMIModelPolicy(native.capabilities, lambda _: None, deadline_monotonic=whole_deadline)
        receipt["model_identity"] = shared.prepare()
        template = shared.policy
        require(shared.selection_id == spec["selection_id"]
                and shared.identity["checkpoint_sha256"] == spec["checkpoint_sha256"]
                and shared.identity["exported_adapter_sha256"] == spec["exported_adapter_sha256"],
                "Actual authenticated model differs from parity spec")
        original_backend = template.backend
        tokenizer = ImmutableTokenizerLength(template.tokenizer)
        template.tokenizer = tokenizer
        receipt["initial_tokenizer_custody"] = tokenizer.verify_unchanged()
        emit({"type": "loaded", "seconds": time.monotonic() - started})
        prompts = json.loads(Path(spec["prompts_path"]).read_text())["prompts"]
        require([row["trace_index"] for row in prompts] == spec["trace_indices"], "Prompt ordering changed")
        for item in prompts:
            emit({"type": "prompt_start", "index": item["trace_index"]})
            prompt_started = time.monotonic()
            prompt_deadline = min(prompt_started + PROMPT_SECONDS, whole_deadline)
            require(time.monotonic() < prompt_deadline, "Parity whole deadline expired")
            require(template.render_prompt(item["goals"], library_prefix_length=247, focus=0) == item["prompt"],
                    "Pinned literal prompt differs from authenticated trained renderer")
            tokenizer.verify_unchanged()
            observed_ref_mx = RecordingMX(original_backend.mx)
            reference_backend = type(original_backend)(original_backend.model, observed_ref_mx, kind=template.kind)
            reference, reference_logits = run_path(template, item["goals"], reference_backend,
                                                   observed_ref_mx, cached=False, deadline=prompt_deadline)
            require(time.monotonic() < prompt_deadline, "Prompt deadline expired after reference; no retry")
            observed_cache_mx = RecordingMX(original_backend.mx)
            with PerTacticKVBackend(original_backend.model, observed_cache_mx, kind=template.kind,
                                   max_context_tokens=6144, max_new_tokens=MAX_TOKENS) as cached_backend:
                cached, cached_logits = run_path(template, item["goals"], cached_backend,
                                                observed_cache_mx, cached=True, deadline=prompt_deadline)
            cached["backend_cache"] = cached_backend.report()
            comparison = compare(reference, cached, reference_logits, cached_logits, original_backend.mx)
            require(time.monotonic() < prompt_deadline, "Prompt deadline expired; late parity cannot pass")
            require(template.backend is original_backend, "Original shared backend was replaced")
            row = {"trace_index": item["trace_index"], "prompt_sha256": item["prompt_sha256"],
                   "reference": reference, "cached": cached, "comparison": comparison,
                   "tokenizer_custody": tokenizer.verify_unchanged(),
                   "seconds": time.monotonic() - prompt_started}
            record_pin = save(out, "prompt-%02d.json" % item["trace_index"], row)
            results.append({**record_pin, "token_gate_passed": comparison["token_gate_passed"],
                            "bitwise_logits_equal": comparison["bitwise_logits_equal"]})
            del reference_logits, cached_logits
            emit({"type": "prompt_done", "index": item["trace_index"], **record_pin,
                  "token_gate_passed": comparison["token_gate_passed"]})
        receipt.update(status="completed", prompts=results,
                       all_four_token_gates_passed=len(results) == 4 and all(x["token_gate_passed"] for x in results),
                       all_four_bitwise_logits_equal=len(results) == 4 and all(x["bitwise_logits_equal"] for x in results),
                       automatic_activation=False,
                       conclusion="Token agreement is a prerequisite only; root review and a fresh fair panel are required for any changed decoder.")
    except Exception as exc:
        receipt.update(status="failed", error_type=type(exc).__name__, error=str(exc)[:1500], prompts=results,
                       all_four_token_gates_passed=False)
    finally:
        emit({"type": "finalize_start"})
        try:
            if shared is not None:
                receipt["loader_final_custody"] = shared.finalize()
                receipt["loader_report_scope"] = "Authentication only; actual parity forwards are recorded separately in each path."
                if shared.policy is not None and isinstance(shared.policy.tokenizer, ImmutableTokenizerLength):
                    receipt["final_tokenizer_custody"] = shared.policy.tokenizer.verify_unchanged()
            read_spec(args.spec, args.spec_sha256)
            receipt["final_source_custody"] = "unchanged"
        except Exception as exc:
            receipt.update(status="failed", custody_error=str(exc)[:1500], all_four_token_gates_passed=False)
        receipt["seconds"] = time.monotonic() - started
        if receipt["seconds"] >= WHOLE_SECONDS:
            receipt.update(status="failed", error="Whole parity deadline exceeded", all_four_token_gates_passed=False)
        saved = save(out, "PARITY_RESULT.json", receipt)
        emit({"type": "done", "status": receipt["status"], **saved})
    return 0 if receipt["status"] == "completed" else 1


def run(args):
    spec = read_spec(args.spec, args.spec_sha256)
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    command = [spec["runtime_python"], "-I", "-B", str(Path(__file__).resolve()), "child",
               "--spec", str(Path(args.spec).resolve()), "--spec-sha256", args.spec_sha256, "--output", str(out)]
    started = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    selector = selectors.DefaultSelector()
    for key, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, key)
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    pending = bytearray()
    phase, phase_started, last_sample, peak = "load", started, 0.0, 0
    error = None
    events = []
    try:
        while selector.get_map():
            now = time.monotonic()
            require(now - started < WHOLE_SECONDS and now - phase_started < PHASE_LIMITS[phase],
                    "Parity parent wall/phase watchdog expired")
            if now - last_sample >= 0.5 and process.poll() is None:
                sampled = subprocess.run(["/bin/ps", "-o", "rss=", "-p", str(process.pid)],
                                         capture_output=True, timeout=2, check=False)
                text = sampled.stdout.decode().strip()
                if text:
                    rss = int(text) * 1024
                    peak = max(peak, rss)
                    require(rss <= MAX_RSS_BYTES, "Parity child exceeded sampled RSS bound")
                else:
                    require(process.poll() is not None, "Cannot independently sample active parity process")
                last_sample = now
            for key, _ in selector.select(0.1):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffers[key.data].extend(chunk)
                require(len(buffers[key.data]) <= 2 * 1024**2, "Parity child output exceeded bound")
                if key.data == "stdout":
                    pending.extend(chunk)
                    while b"\n" in pending:
                        line, _, rest = pending.partition(b"\n")
                        pending[:] = rest
                        event = json.loads(line)
                        events.append(event)
                        if event.get("type") == "prompt_start":
                            phase, phase_started = "prompt", time.monotonic()
                        elif event.get("type") == "finalize_start":
                            phase, phase_started = "finalize", time.monotonic()
                        print(json.dumps(event), flush=True)
        process.wait(timeout=5)
    except BaseException as exc:
        error = type(exc).__name__ + ": " + str(exc)[:1000]
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        selector.close()
        for stream in (process.stdout, process.stderr):
            stream.close()
        try:
            os.killpg(process.pid, 0)
            quiescent = False
        except ProcessLookupError:
            quiescent = True
        except PermissionError:
            quiescent = False
        for name, content in buffers.items():
            with (out / ("child." + name)).open("xb") as stream:
                stream.write(content)
        completed = (error is None and process.returncode == 0 and quiescent
                     and time.monotonic() - started < WHOLE_SECONDS
                     and len(events) > 0 and events[-1].get("type") == "done"
                     and events[-1].get("status") == "completed")
        receipt = {"schema": "hydra-parity-supervisor-v1", "command": command, "spec_sha256": args.spec_sha256,
            "actual_pid": process.pid, "actual_exit_code": process.returncode, "error": error,
            "quiescent": quiescent, "peak_sampled_rss_bytes": peak,
            "seconds": time.monotonic() - started, "events": events,
            "status": "completed" if completed else "failed", "automatic_retry": False,
            "activation": False, "quality_claim": False}
        save(out, "SUPERVISOR.json", receipt)
        print(json.dumps({"supervisor_status": receipt["status"], "actual_exit_code": process.returncode,
                          "quiescent": quiescent, "output": str(out)}), flush=True)
    return 0 if completed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "child"))
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--spec-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments) if arguments.mode == "run" else child(arguments))
