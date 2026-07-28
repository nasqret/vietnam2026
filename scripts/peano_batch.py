#!/usr/bin/env python3
"""Run a finite Peano Lab proof batch in one warm, browser-free process.

Generation example::

    python3 scripts/peano_batch.py --trace-output run.trace.jsonl \
      < requests.jsonl > results.jsonl

The raw binding v1 trace and compact result envelopes are deliberately
separate artifacts.  Results are transactionally staged until EOF and, in
generation mode, until the complete trace artifact commits.  This is not a
duplex request/response service.  ``--verify-only`` is the explicit faster
path for checking already-authored scripts when transition training data is
unwanted.  By default, exit status zero means that the protocol completed;
individual ``open`` and tactic-failure statuses remain ordinary result rows.
Use ``--require-proved`` when CI should require every executed proof to close.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.batch import (  # noqa: E402
    BATCH_VERSION,
    MODEL_V1_COMMANDS,
    MODEL_V1_THEOREMS,
    BatchRequestError,
    capability_sha256,
    execute_request,
    request_error,
)
from peano_lab.library.theorems import THEOREMS  # noqa: E402
from peano_lab.ui.prove import (  # noqa: E402
    FULL_SURFACE_CAPABILITIES,
    SurfaceCapabilities,
)


MAX_JSONL_LINE_BYTES = 1_000_000
MAX_JSON_INTEGER_DIGITS = 128
DEFAULT_MAX_INPUT_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_REQUESTS = 10_000
DEFAULT_MAX_RESULT_BYTES = 128 * 1024 * 1024
DEFAULT_MAX_TRACE_BYTES = 512 * 1024 * 1024
LIBRARY_NAMES = frozenset(spec.name for spec in THEOREMS)


class _BatchLimitError(RuntimeError):
    """A finite transactional batch exhausted a runner-owned aggregate limit."""


class _BoundedTraceSink:
    """Reject the trace record that would cross the aggregate UTF-8 ceiling."""

    __slots__ = ("_stream", "_limit", "bytes_written")

    def __init__(self, stream: object, limit: int) -> None:
        self._stream = stream
        self._limit = limit
        self.bytes_written = 0

    def write(self, text: str) -> int:
        encoded_size = len(text.encode("utf-8"))
        next_size = self.bytes_written + encoded_size
        if next_size > self._limit:
            raise _BatchLimitError(
                "raw trace exceeds the aggregate "
                f"{self._limit}-byte batch limit"
            )
        accepted = self._stream.write(text)  # type: ignore[attr-defined]
        if type(accepted) is int and accepted == len(text):
            self.bytes_written = next_size
        elif accepted is None:
            self.bytes_written = next_size
        return accepted  # type: ignore[return-value]


def _positive_limit(value: str) -> int:
    """Argparse converter for explicit, finite aggregate byte/count limits."""

    try:
        parsed = int(value, 10)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive integer") from None
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "read a finite transactional Peano Lab JSONL batch from stdin; "
            "compact results are withheld until EOF and trace commit"
        ),
        epilog=(
            "This is a bounded file/batch transport, not an interactive duplex "
            "request/response protocol. Exit 0 means protocol completion, not "
            "that every proof closed; use --require-proved for verification/CI."
        ),
    )
    parser.add_argument(
        "--trace-output",
        type=Path,
        metavar="PATH",
        help="new file for contiguous raw v1 traces (required unless --verify-only)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="check scripts without retaining transition traces",
    )
    parser.add_argument(
        "--environment",
        choices=("full", "model-v1"),
        default="full",
        help="fixed tactic environment for every request (default: full)",
    )
    parser.add_argument(
        "--allow-theorem",
        action="append",
        default=[],
        metavar="NAME",
        help="additional checked theorem available to model-v1 (repeatable)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="stop on the first malformed request instead of emitting request_error",
    )
    parser.add_argument(
        "--require-proved",
        action="store_true",
        help=(
            "exit 1 after normal publication if any executed result is not proved"
        ),
    )
    parser.add_argument(
        "--max-input-bytes",
        type=_positive_limit,
        default=DEFAULT_MAX_INPUT_BYTES,
        metavar="N",
        help=(
            "maximum aggregate UTF-8 input bytes, including blank and malformed "
            f"lines (default: {DEFAULT_MAX_INPUT_BYTES})"
        ),
    )
    parser.add_argument(
        "--max-requests",
        type=_positive_limit,
        default=DEFAULT_MAX_REQUESTS,
        metavar="N",
        help=(
            "maximum nonblank request records in one transaction "
            f"(default: {DEFAULT_MAX_REQUESTS})"
        ),
    )
    parser.add_argument(
        "--max-result-bytes",
        type=_positive_limit,
        default=DEFAULT_MAX_RESULT_BYTES,
        metavar="N",
        help=(
            "maximum aggregate staged result JSONL bytes "
            f"(default: {DEFAULT_MAX_RESULT_BYTES})"
        ),
    )
    parser.add_argument(
        "--max-trace-bytes",
        type=_positive_limit,
        default=DEFAULT_MAX_TRACE_BYTES,
        metavar="N",
        help=(
            "maximum aggregate raw trace UTF-8 bytes "
            f"(default: {DEFAULT_MAX_TRACE_BYTES})"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"peano-batch {BATCH_VERSION}",
    )
    return parser


def _capabilities(args: argparse.Namespace, parser: argparse.ArgumentParser):
    repeated = sorted(
        {name for name in args.allow_theorem if args.allow_theorem.count(name) > 1}
    )
    if repeated:
        parser.error("repeated --allow-theorem: " + ", ".join(repeated))
    unknown = sorted(set(args.allow_theorem) - LIBRARY_NAMES)
    if unknown:
        parser.error("unknown --allow-theorem: " + ", ".join(unknown))
    if args.environment == "full":
        if args.allow_theorem:
            parser.error("--allow-theorem is only valid with --environment model-v1")
        return FULL_SURFACE_CAPABILITIES
    return SurfaceCapabilities(
        label="model-v1",
        allowed_commands=MODEL_V1_COMMANDS,
        allowed_theorems=frozenset(MODEL_V1_THEOREMS) | frozenset(args.allow_theorem),
    )


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise BatchRequestError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str):
    raise BatchRequestError(f"non-finite JSON number is not allowed: {value}")


def _parse_int(value: str) -> int:
    digits = value[1:] if value.startswith("-") else value
    if len(digits) > MAX_JSON_INTEGER_DIGITS:
        raise BatchRequestError(
            "JSON integer exceeds the "
            f"{MAX_JSON_INTEGER_DIGITS}-digit transport limit"
        )
    return int(value, 10)


def _reject_float(value: str):
    raise BatchRequestError(f"JSON floating-point numbers are not allowed: {value}")


def _decode(raw: str) -> object:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_int=_parse_int,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except RecursionError:
        raise BatchRequestError("JSON nesting exceeds the decoder limit") from None


def _session_id(
    request: object,
    *,
    ordinal: int,
    environment_sha256: str,
) -> str:
    try:
        payload = json.dumps(
            [BATCH_VERSION, environment_sha256, ordinal, request],
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (RecursionError, TypeError, ValueError) as exc:
        raise BatchRequestError(
            f"request cannot be deterministically hashed: {type(exc).__name__}"
        ) from None
    return "peano-batch-" + hashlib.sha256(payload).hexdigest()[:24]


def _encoded_line(record: dict[str, object]) -> bytes:
    line = json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n"
    return line.encode("ascii")


def _stage_result(
    record: dict[str, object],
    stream: object,
    bytes_written: int,
    byte_limit: int,
) -> int:
    """Append one complete envelope without crossing the aggregate ceiling."""

    encoded = _encoded_line(record)
    next_size = bytes_written + len(encoded)
    if next_size > byte_limit:
        raise _BatchLimitError(
            f"result JSONL exceeds the aggregate {byte_limit}-byte batch limit"
        )
    accepted = stream.write(encoded)  # type: ignore[attr-defined]
    if type(accepted) is not int or accepted != len(encoded):
        raise OSError(
            f"result staging accepted {accepted!r} of {len(encoded)} bytes"
        )
    return next_size


def _publish_results(stream: object) -> None:
    stream.flush()  # type: ignore[attr-defined]
    stream.seek(0)  # type: ignore[attr-defined]
    binary = getattr(sys.stdout, "buffer", None)
    while chunk := stream.read(128 * 1024):  # type: ignore[attr-defined]
        if binary is not None:
            binary.write(chunk)
        else:
            sys.stdout.write(chunk.decode("ascii"))
    (binary or sys.stdout).flush()


def _write_error(text: str) -> None:
    """Keep diagnostics printable even under an ASCII cluster locale."""

    safe = text.encode("ascii", "backslashreplace").decode("ascii")
    sys.stderr.write(safe)
    sys.stderr.flush()


def _input_lines():
    """Yield bounded physical lines plus their exact transport byte cost."""

    binary = getattr(sys.stdin, "buffer", None)
    if binary is None:
        for line_number, raw in enumerate(sys.stdin, 1):
            try:
                encoded = raw.encode("utf-8")
            except UnicodeEncodeError:
                yield line_number, None, BatchRequestError(
                    f"line {line_number} is not valid UTF-8"
                ), len(raw.encode("utf-8", errors="surrogatepass"))
                continue
            if len(encoded) > MAX_JSONL_LINE_BYTES:
                yield line_number, None, BatchRequestError(
                    f"line {line_number} exceeds the "
                    f"{MAX_JSONL_LINE_BYTES}-byte limit"
                ), len(encoded)
                continue
            yield line_number, raw, None, len(encoded)
        return

    line_number = 0
    while True:
        raw = binary.readline(MAX_JSONL_LINE_BYTES + 2)
        if not raw:
            return
        line_number += 1
        consumed = len(raw)
        if len(raw) > MAX_JSONL_LINE_BYTES:
            while raw and not raw.endswith(b"\n"):
                raw = binary.readline(MAX_JSONL_LINE_BYTES + 2)
                consumed += len(raw)
            yield line_number, None, BatchRequestError(
                f"line {line_number} exceeds the {MAX_JSONL_LINE_BYTES}-byte limit"
            ), consumed
            continue
        try:
            decoded = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            yield line_number, None, BatchRequestError(
                f"line {line_number} is not valid UTF-8"
            ), consumed
            continue
        yield line_number, decoded, None, consumed


def _batch_limit_cause(error: BaseException) -> _BatchLimitError | None:
    """Recover an aggregate-limit error wrapped by the checked trace sink."""

    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        if isinstance(current, _BatchLimitError):
            return current
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return None


def _open_trace_stage(
    target: Path,
    parser: argparse.ArgumentParser,
) -> tuple[Path, object]:
    """Open a hidden same-directory staging file without touching ``target``."""

    if os.path.lexists(target):
        parser.error(f"trace output already exists: {target}")
    parent = target.parent
    if not parent.is_dir():
        parser.error(f"trace output directory does not exist: {parent}")
    try:
        descriptor, raw_stage = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".partial",
            dir=parent,
        )
    except OSError as exc:
        parser.error(f"cannot stage trace output {target}: {exc}")
    stage = Path(raw_stage)
    try:
        stream = os.fdopen(descriptor, "w", encoding="utf-8", newline="\n")
    except BaseException:
        os.close(descriptor)
        stage.unlink(missing_ok=True)
        raise
    return stage, stream


def _close_trace_stage(stream: object) -> None:
    """Durably finish all buffered writes before an artifact may be published."""

    try:
        stream.flush()  # type: ignore[attr-defined]
        os.fsync(stream.fileno())  # type: ignore[attr-defined]
    except BaseException:
        # Cleanup is permitted to catch control-flow exceptions only when it
        # immediately re-raises the original interruption.
        try:
            stream.close()  # type: ignore[attr-defined]
        except Exception:
            pass
        raise
    stream.close()  # type: ignore[attr-defined]


def _publish_trace_stage(stage: Path, target: Path) -> None:
    """Atomically commit without replacing; cleanup is deliberately separate."""

    os.link(stage, target)


def _fsync_directory(directory: Path) -> None:
    """Persist a directory-entry change and always close its descriptor."""

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _discard_interrupted_transaction(
    trace_stream: object | None,
    result_stage: object,
    trace_stage: Path | None,
) -> None:
    """Best-effort cleanup followed by caller re-raising the interruption."""

    for stream in (trace_stream, result_stage):
        if stream is None:
            continue
        try:
            stream.close()  # type: ignore[attr-defined]
        except Exception:
            pass
    if trace_stage is not None:
        try:
            trace_stage.unlink(missing_ok=True)
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    mode = "verify" if args.verify_only else "trace"
    capabilities = _capabilities(args, parser)
    environment_sha256 = capability_sha256(capabilities)
    if args.verify_only and args.trace_output is not None:
        parser.error("--trace-output is incompatible with --verify-only")
    if not args.verify_only and args.trace_output is None:
        parser.error("--trace-output is required for generation")

    trace_stream = None
    trace_sink = None
    trace_stage: Path | None = None
    result_stage = tempfile.TemporaryFile(mode="w+b")
    if args.trace_output is not None:
        trace_stage, trace_stream = _open_trace_stage(args.trace_output, parser)
        trace_sink = _BoundedTraceSink(trace_stream, args.max_trace_bytes)

    exit_code = 0
    completed_sessions = 0
    has_unproved_result = False
    publish_trace = True
    publish_results = True
    fatal_error: Exception | None = None
    result_bytes = 0
    input_bytes = 0
    try:
        ordinal = 0
        for line_number, raw, transport_error, transport_bytes in _input_lines():
            input_bytes += transport_bytes
            if input_bytes > args.max_input_bytes:
                raise _BatchLimitError(
                    "input exceeds the aggregate "
                    f"{args.max_input_bytes}-byte batch limit"
                )
            if transport_error is None and raw is not None and not raw.strip():
                continue
            if ordinal >= args.max_requests:
                raise _BatchLimitError(
                    "request count exceeds the aggregate "
                    f"{args.max_requests}-record batch limit"
                )
            ordinal += 1
            request: object = None
            request_id: object = ""
            try:
                if transport_error is not None:
                    raise transport_error
                if raw is None:  # pragma: no cover - generator invariant guard
                    raise BatchRequestError(f"line {line_number} has no request text")
                request = _decode(raw)
                if isinstance(request, dict):
                    request_id = request.get("id", "")
                result = execute_request(
                    request,  # type: ignore[arg-type]
                    mode=mode,
                    capabilities=capabilities,
                    trace_sink=trace_sink,
                    session_id=_session_id(
                        request,
                        ordinal=ordinal,
                        environment_sha256=environment_sha256,
                    ),
                )
            except (BatchRequestError, json.JSONDecodeError) as exc:
                if args.fail_fast:
                    safe_error = request_error(
                        request_id,
                        exc,
                        mode=mode,
                        surface=capabilities.label,
                        environment_sha256=environment_sha256,
                    )["error"]
                    _write_error(f"line {line_number}: {safe_error}\n")
                    exit_code = 2
                    publish_trace = False
                    publish_results = False
                    break
                result_bytes = _stage_result(
                    request_error(
                        request_id,
                        exc,
                        mode=mode,
                        surface=capabilities.label,
                        environment_sha256=environment_sha256,
                    ),
                    result_stage,
                    result_bytes,
                    args.max_result_bytes,
                )
                continue
            completed_sessions += 1
            has_unproved_result = has_unproved_result or result.status != "proved"
            result_bytes = _stage_result(
                result.to_dict(include_trace=False),
                result_stage,
                result_bytes,
                args.max_result_bytes,
            )
            if result.status == "kernel_rejection":
                _write_error(
                    f"line {line_number}: independent kernel rejection; stopping\n"
                )
                exit_code = 3
                break
    except (KeyboardInterrupt, SystemExit):
        _discard_interrupted_transaction(trace_stream, result_stage, trace_stage)
        raise
    except Exception as exc:
        limit_error = _batch_limit_cause(exc)
        if limit_error is not None:
            # A controlled exhaustion invalidates the finite transaction.  Its
            # bounded hidden stage is disposable rather than a crash artifact.
            publish_trace = False
            publish_results = False
            exit_code = 2
            _write_error(f"batch limit exceeded: {limit_error}\n")
        else:
            # A partially written trace is useful for diagnosis, but it must
            # never appear at the requested final path or enter a dataset.
            fatal_error = exc
            publish_trace = False
            publish_results = False
            exit_code = 4
            safe_error = request_error("", exc)["error"]
            _write_error(
                f"fatal batch error: {type(exc).__name__}: {safe_error}\n"
            )

    if completed_sessions == 0:
        publish_trace = False
        if exit_code == 0:
            exit_code = 2

    if trace_stream is not None:
        try:
            _close_trace_stage(trace_stream)
        except (KeyboardInterrupt, SystemExit):
            _discard_interrupted_transaction(trace_stream, result_stage, trace_stage)
            raise
        except Exception as exc:
            fatal_error = fatal_error or exc
            publish_trace = False
            publish_results = False
            exit_code = 4
            safe_error = request_error("", exc)["error"]
            _write_error(
                f"fatal trace finalization error: {type(exc).__name__}: "
                f"{safe_error}\n"
            )

    trace_published = args.verify_only
    committed_stage: Path | None = None
    if trace_stage is not None and args.trace_output is not None:
        if publish_trace:
            try:
                _publish_trace_stage(trace_stage, args.trace_output)
            except (KeyboardInterrupt, SystemExit):
                # ``link`` is the commit point.  If interruption arrived just
                # after it, unlinking the staging name preserves the complete
                # committed target; if it arrived before, no target exists.
                _discard_interrupted_transaction(
                    trace_stream, result_stage, trace_stage
                )
                raise
            except OSError as exc:
                fatal_error = fatal_error or exc
                publish_results = False
                exit_code = 4
                _write_error(
                    f"cannot publish trace output {args.trace_output}: {exc}; "
                    f"incomplete staging file retained at {trace_stage}\n"
                )
            else:
                # The hard link is the irreversible commit point.  Matching
                # result rows may now be exposed even if later cleanup fails.
                trace_published = True
                committed_stage = trace_stage
                try:
                    _fsync_directory(args.trace_output.parent)
                except (KeyboardInterrupt, SystemExit):
                    _discard_interrupted_transaction(
                        trace_stream, result_stage, trace_stage
                    )
                    raise
                except OSError as exc:
                    exit_code = 4
                    _write_error(
                        f"trace output {args.trace_output} committed, but its "
                        f"directory sync failed: {exc}\n"
                    )
        elif fatal_error is None:
            # Empty, all-invalid, and deliberate fail-fast batches have no
            # complete artifact. Controlled aggregate-limit exhaustion is
            # equally disposable. Unexpected failures retain their hidden
            # partial file for diagnosis.
            try:
                trace_stage.unlink(missing_ok=True)
            except (KeyboardInterrupt, SystemExit):
                _discard_interrupted_transaction(
                    trace_stream, result_stage, trace_stage
                )
                raise

    if publish_results and (trace_published or completed_sessions == 0):
        try:
            _publish_results(result_stage)
        except (KeyboardInterrupt, SystemExit):
            _discard_interrupted_transaction(
                trace_stream, result_stage, trace_stage
            )
            raise

    if committed_stage is not None:
        try:
            committed_stage.unlink()
        except (KeyboardInterrupt, SystemExit):
            _discard_interrupted_transaction(
                trace_stream, result_stage, trace_stage
            )
            raise
        except OSError as exc:
            exit_code = 4
            _write_error(
                f"trace output {args.trace_output} is committed, but staging "
                f"cleanup failed at {committed_stage}: {exc}\n"
            )
        else:
            try:
                _fsync_directory(committed_stage.parent)
            except (KeyboardInterrupt, SystemExit):
                _discard_interrupted_transaction(
                    trace_stream, result_stage, trace_stage
                )
                raise
            except OSError as exc:
                exit_code = 4
                _write_error(
                    f"trace output {args.trace_output} is committed, but staging "
                    f"cleanup sync failed: {exc}\n"
                )
    if args.require_proved and has_unproved_result and exit_code == 0:
        exit_code = 1
    result_stage.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
