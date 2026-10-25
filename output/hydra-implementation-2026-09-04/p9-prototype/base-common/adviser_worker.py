"""Fixed child entrypoint. Never accepts code, arbitrary argv, or theorem text."""
from pathlib import Path
import hashlib
import os
import resource
import signal
import sys


APP = Path(__file__).resolve().parent


def _audit(event, args):
    denied = {"subprocess.Popen", "os.fork", "os.forkpty", "os.posix_spawn", "os.system", "os.exec",
              "os.kill", "os.killpg", "os.chdir", "os.remove", "os.rmdir", "os.rename", "os.mkdir",
              "os.link", "os.symlink", "os.chmod", "os.chown", "os.truncate"}
    if event in denied or event.startswith("socket."):
        raise PermissionError("The adviser helper is offline, read-only and cannot start or signal processes.")
    if event == "open":
        _, mode, flags = args
        writing = (type(mode) is str and any(char in mode for char in "wax+"))
        writing |= type(flags) is int and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
        if writing:
            raise PermissionError("The adviser helper cannot open writable files.")


def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--backend" or sys.argv[2] not in {"sympy", "cvc5"}:
        raise SystemExit(64)
    backend = sys.argv[2]
    cpu, wall = (1, 2) if backend == "sympy" else (6, 8)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    signal.alarm(wall)
    sys.path.insert(0, str(APP))
    from adviser_protocol import (MAX_INPUT, POLICY, RESPONSE_SCHEMA, SCHEMA, ProtocolError,
                                  canonical_json, read_json)
    from adviser_process import backend_identity, package, package_directory
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    if not 0 < len(raw) <= MAX_INPUT:
        raise ProtocolError("Adviser stdin exceeds 64 KiB.")
    request = read_json(raw, MAX_INPUT)
    identity = backend_identity(backend)
    if (type(request) is not dict or set(request) != {"schema", "backend", "identity", "policy", "semantic_context", "payload"}
            or request["schema"] != SCHEMA or request["backend"] != backend
            or request["identity"] != identity or request["policy"] != POLICY):
        raise ProtocolError("The fixed helper received a different backend/source request.")
    context = canonical_json(request["semantic_context"], MAX_INPUT)
    if request["semantic_context"].get("schema") != "hydra-adviser-semantic-context-v1":
        raise ProtocolError("Missing full semantic context binding.")
    package(backend=backend, verify_files=True)
    sys.path.insert(0, str(package_directory(backend)))
    sys.addaudithook(_audit)
    if backend == "sympy":
        from sympy_bridge import solve_payload
    else:
        from smt_bridge import solve_payload
    proposal = solve_payload(request["payload"])
    response = {"schema": RESPONSE_SCHEMA, "backend": backend, "identity": identity,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "context_sha256": hashlib.sha256(context).hexdigest(), "kernel_checked": False, **proposal}
    encoded = canonical_json(response, 256 * 1024)
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # No complete response accompanies helper errors; parent exit authority
        # overrules any partial bytes already emitted, including apparent proofs.
        sys.stderr.write(type(error).__name__ + ": " + str(error)[:400] + "\n")
        raise SystemExit(70)
